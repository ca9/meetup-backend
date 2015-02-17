package iiitd.ac.in.dsys.meetup;

import android.accounts.AccountManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;

import com.appspot.intense_terra_821.users_api.UsersApi;
import com.appspot.intense_terra_821.users_api.UsersApiRequest;
import com.appspot.intense_terra_821.users_api.UsersApiRequestInitializer;
import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.GooglePlayServicesUtil;
import com.google.android.gms.gcm.GoogleCloudMessaging;
import com.google.api.client.extensions.android.http.AndroidHttp;
import com.google.api.client.googleapis.extensions.android.gms.auth.GoogleAccountCredential;
import com.google.api.client.http.HttpHeaders;
import com.google.api.client.json.gson.GsonFactory;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collection;
import java.util.concurrent.atomic.AtomicInteger;

import iiitd.ac.in.dsys.meetup.messages.firstLoginTask;
import iiitd.ac.in.dsys.meetup.messages.pingHelloTask;


public class MainActivity extends ActionBarActivity {
    Context context;
    private SharedPreferences settings;
    String TAG="MainActivity";

    //GCM and Play Services
    static final int REQUEST_CODE_PICK_ACCOUNT = 1000;
    static final int REQUEST_CODE_RECOVER_FROM_PLAY_SERVICES_ERROR = 1001;
    private final static int PLAY_SERVICES_RESOLUTION_REQUEST = 9000;

    public static final String EXTRA_MESSAGE = "message";
    public static final String PROPERTY_REG_ID = "registration_id";
    private static final String PROPERTY_APP_VERSION = "appVersion";
    private static final String PROPERTY_OAUTH_TOKEN="OAuthToken";
    String SENDER_ID = "812458715891";

    GoogleCloudMessaging gcm;
    AtomicInteger msgId = new AtomicInteger();
    SharedPreferences prefs;

    String regid;

    //Cloud Endpoints
    // Services
    UsersApi usersApiInst;

    // Credentials, client ID, Authorization
    GoogleAccountCredential credential;
    private String accountEmail;
    private static final int REQUEST_ACCOUNT_PICKER = 2;
    public static final String WEB_CLIENT_ID = "812458715891-p8e6e4oqph65matkdr1v06r02vtri1du.apps.googleusercontent.com";
    // Unused
    public static final String ANDROID_CLIENT_ID = "812458715891-cd592i6lgul160gf15ma2tbb1oj4k4k2.apps.googleusercontent.com";


    // Scopes
    public static final String EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email";
    public static final String CONTACTS_SCOPE = "https://www.googleapis.com/auth/contacts.readonly";
    public static final Collection<String> SCOPES = Arrays.asList("server:client_id:" + WEB_CLIENT_ID, EMAIL_SCOPE, CONTACTS_SCOPE);


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        context=this;
        // fetch settings
        settings = getSharedPreferences("MeetupPreferences", 0);
        // set Credentials (Pick chosen Account)
        setCredentials();
        // add UI Callbacks
        setUICallbacks();
        // build services. Set the first param to true to test locally. Second param is local IP of server.
        buildApiServices(false, "192.168.1.6");

        // Check device for Play Services APK.
        if (checkPlayServices()) {
            gcm = GoogleCloudMessaging.getInstance(this);
            regid = getRegistrationId(context);

            if (regid.isEmpty()) {
                registerInBackground();
            }
            else {
                Log.v(TAG, "Already registered to GCM");
            }
        } else {
            Log.i(TAG, "No valid Google Play Services APK found.");
        }
    }

    // You need to do the Play Services APK check here too.
    @Override
    protected void onResume() {
        super.onResume();
        checkPlayServices();
    }

    /**
     * Check the device to make sure it has the Google Play Services APK. If
     * it doesn't, display a dialog that allows users to download the APK from
     * the Google Play Store or enable it in the device's system settings.
     */
    private boolean checkPlayServices() {
        int resultCode = GooglePlayServicesUtil.isGooglePlayServicesAvailable(this);
        if (resultCode != ConnectionResult.SUCCESS) {
            if (GooglePlayServicesUtil.isUserRecoverableError(resultCode)) {
                GooglePlayServicesUtil.getErrorDialog(resultCode, this,
                        PLAY_SERVICES_RESOLUTION_REQUEST).show();
            } else {
                Log.i(TAG, "This device is not supported.");
                finish();
            }
            return false;
        }
        return true;
    }

    /**
     * Gets the current registration ID for application on GCM service.
     * <p>
     * If result is empty, the app needs to register.
     *
     * @return registration ID, or empty string if there is no existing
     *         registration ID.
     */
    private String getRegistrationId(Context context) {
        final SharedPreferences prefs = getLoginPreferences(context);
        String registrationId = prefs.getString(PROPERTY_REG_ID, "");
        if (registrationId.isEmpty()) {
            Log.i(TAG, "Registration not found.");
            return "";
        }
        // Check if app was updated; if so, it must clear the registration ID
        // since the existing regID is not guaranteed to work with the new
        // app version.
        int registeredVersion = prefs.getInt(PROPERTY_APP_VERSION, Integer.MIN_VALUE);
        int currentVersion = getAppVersion(context);
        if (registeredVersion != currentVersion) {
            Log.i(TAG, "App version changed.");
            return "";
        }
        return registrationId;
    }

    /**
     * @return Application's {@code SharedPreferences}.
     */
    private SharedPreferences getLoginPreferences(Context context) {
        return getSharedPreferences(MainActivity.class.getSimpleName(),
                Context.MODE_PRIVATE);
    }

    private int getAppVersion(Context context){
        PackageManager pm=context.getPackageManager();
        int versionNumber=0;
        try {
            PackageInfo pi=pm.getPackageInfo(context.getPackageName(),0);
            versionNumber=pi.versionCode;
        } catch (PackageManager.NameNotFoundException e) {
            e.printStackTrace();
        }
        return versionNumber;
    }

    /**
     * Registers the application with GCM servers asynchronously.
     * <p>
     * Stores the registration ID and app versionCode in the application's
     * shared preferences.
     */
    private void registerInBackground() {
        new AsyncTask<Void,String,String>() {
            @Override
            protected String doInBackground(Void... params) {
                String msg = "";
                try {
                    if (gcm == null) {
                        gcm = GoogleCloudMessaging.getInstance(context);
                    }
                    regid = gcm.register(SENDER_ID);
                    msg = "Device registered, registration ID=" + regid;

                    //                    sendRegistrationIdToBackend();

                    // Persist the regID - no need to register again.
                    storeRegistrationId(context, regid);
                } catch (IOException ex) {
                    msg = "Error :" + ex.getMessage();

                }
                return msg;
            }

            @Override
            protected void onPostExecute(String msg) {
                Log.v(TAG,"GCM Registration ID: "+msg + "\n");
            }
        }.execute(null, null, null);

    }

    /**
     * Stores the registration ID and app versionCode in the application's
     * {@code SharedPreferences}.
     *
     * @param context application's context.
     * @param regId registration ID
     */
    private void storeRegistrationId(Context context, String regId) {
        final SharedPreferences prefs = getLoginPreferences(context);
        int appVersion = getAppVersion(context);
        Log.i(TAG, "Saving regId on app version " + appVersion);
        SharedPreferences.Editor editor = prefs.edit();
        editor.putString(PROPERTY_REG_ID, regId);
        editor.putInt(PROPERTY_APP_VERSION, appVersion);
        editor.commit();
    }


    private void setUICallbacks() {
        ((Button) findViewById(R.id.pingButton)).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                (new pingHelloTask(MainActivity.this, usersApiInst)).execute();
            }
        });
        ((Button) findViewById(R.id.firstLogin)).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                (new firstLoginTask(MainActivity.this, usersApiInst,
                        regid,         // Regid
                        accountEmail,   // Full Name
                        "9654505022"    // Phone Number
                )).execute();
            }
        });
    }

    public void onPing(View v) {
        // Works like a charm.
        (new pingHelloTask(MainActivity.this, usersApiInst)).execute();
        // (new firstLoginTask(MainActivity.this, usersApiInst, "12897638162", "Aditya", "9654505022")).execute();
    }

    // setAccountEmail definition
    private void setAccountEmail(String accountEmail) {
        SharedPreferences.Editor editor = settings.edit();
        editor.putString("ACCOUNT_NAME", accountEmail);
        editor.commit();
        credential.setSelectedAccountName(accountEmail);
        this.accountEmail = accountEmail;
    }

    private void setCredentials() {
        credential = GoogleAccountCredential.usingAudience(this.getApplicationContext(), "server:client_id:" + WEB_CLIENT_ID);
        // credential = GoogleAccountCredential.usingOAuth2(this, SCOPES);
        credential.setSelectedAccountName(settings.getString("ACCOUNT_NAME", null));
        if (credential.getSelectedAccountName() != null) {
            // Already signed in, begin app!
            //Toast.makeText(getBaseContext(), "Logged in with : " + credential.getSelectedAccountName(), Toast.LENGTH_SHORT).show();
            this.accountEmail = credential.getSelectedAccountName();
            Log.v(TAG,"Email stored: "+this.accountEmail);
        } else {
            // Else request a selection.
            startActivityForResult(credential.newChooseAccountIntent(), REQUEST_ACCOUNT_PICKER);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        switch (requestCode) {
            case REQUEST_ACCOUNT_PICKER:
                if (data != null && data.getExtras() != null) {
                    String accountName =
                            data.getExtras().getString(
                                    AccountManager.KEY_ACCOUNT_NAME);
                    if (accountName != null) {
                        setAccountEmail(accountName);
                        Toast.makeText(getBaseContext(), "Logged in with : " + credential.getSelectedAccountName(), Toast.LENGTH_SHORT).show();
                    }
                }
                break;
        }
    }


    private void buildApiServices(boolean local, String IP) {
        UsersApi.Builder userApiBuilder = new UsersApi.Builder(
                AndroidHttp.newCompatibleTransport(),
                new GsonFactory(),
                // null works
                credential);
        if (local) {
            userApiBuilder.setGoogleClientRequestInitializer(new UsersApiRequestInitializer() {
                @Override
                // Because the dev-server cannot handle GZip.
                // http://stackoverflow.com/questions/15393363/how-to-disable-gzipcontent-in-cloud-endpoints-builder-in-android
                // https://code.google.com/p/googleappengine/issues/detail?id=9140
                protected void initializeUsersApiRequest(UsersApiRequest<?> request) {
                    request.setDisableGZipContent(true);
                    // Add email because endpoints sucks.
                    request.setRequestHeaders(new HttpHeaders().set("ENDPOINTS_AUTH_EMAIL", settings.getString("ACCOUNT_NAME", null)));
                }
            });
            usersApiInst = userApiBuilder.setRootUrl("http://" + IP + ":8080/_ah/api").build();
        } else {
            usersApiInst = userApiBuilder.build();
        }

    }

}
