package in.ac.iiitd.dsys.meetup;

import android.accounts.AccountManager;
import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.telephony.TelephonyManager;
import android.util.Log;
import android.view.View;
import android.widget.Toast;

import com.google.android.gms.auth.GoogleAuthException;
import com.google.android.gms.auth.GoogleAuthUtil;
import com.google.android.gms.auth.GooglePlayServicesAvailabilityException;
import com.google.android.gms.auth.UserRecoverableAuthException;
import com.google.android.gms.common.AccountPicker;
import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.GooglePlayServicesUtil;
import com.google.android.gms.gcm.GoogleCloudMessaging;

import org.apache.http.HttpResponse;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.ResponseHandler;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.BasicResponseHandler;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.message.BasicHeader;
import org.apache.http.protocol.HTTP;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.util.concurrent.atomic.AtomicInteger;


public class LoginActivity extends ActionBarActivity {

    static final int REQUEST_CODE_PICK_ACCOUNT = 1000;
    static final int REQUEST_CODE_RECOVER_FROM_PLAY_SERVICES_ERROR = 1001;
    private final static int PLAY_SERVICES_RESOLUTION_REQUEST = 9000;

    public static final String EXTRA_MESSAGE = "message";
    public static final String PROPERTY_REG_ID = "registration_id";
    private static final String PROPERTY_APP_VERSION = "appVersion";
    private static final String PROPERTY_OAUTH_TOKEN="OAuthToken";

    private static final String URL="https://intense-terra-821.appspot.com/_ah/api/";
    private static  final String USER_LOGIN_API=URL+"users_api/v1/firstLogin";

    String SENDER_ID = "812458715891";

    GoogleCloudMessaging gcm;
    AtomicInteger msgId = new AtomicInteger();
    SharedPreferences prefs;

    String regid;

    String mEmail; // Received from newChooseAccountIntent(); passed to getToken()
    String profileName; //Received from GET request on google API

    private static final String SCOPE =
            "oauth2:https://www.googleapis.com/auth/userinfo.profile";

    String TAG="LoginActivity";

    Context context;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        context=getApplicationContext();

        // Check device for Play Services APK.
        if (checkPlayServices()) {
            gcm = GoogleCloudMessaging.getInstance(this);
            regid = getRegistrationId(context);

            if (regid.isEmpty()) {
                registerInBackground();
            }
            else
                Log.v(TAG,"Already registered to GCM");
        } else {
            Log.i(TAG, "No valid Google Play Services APK found.");
        }
        setContentView(R.layout.activity_login);
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
        return getSharedPreferences(LoginActivity.class.getSimpleName(),
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
     * Sends the registration ID to your server over HTTP, so it can use GCM/HTTP
     * or CCS to send messages to your app.
     */
    private void sendRegistrationIdToBackend() {
        new AsyncTask<Void,String,String>() {
            @Override
            protected String doInBackground(Void... params) {
                String msg = "";
                final SharedPreferences prefs = getLoginPreferences(context);
                String regID=prefs.getString(PROPERTY_REG_ID, null);
                String outhToken=prefs.getString(PROPERTY_OAUTH_TOKEN,null);

                TelephonyManager tMgr =(TelephonyManager)context.getSystemService(Context.TELEPHONY_SERVICE);
                String mPhoneNumber = tMgr.getLine1Number();

                Log.v(TAG,"Sending info to backend at: "+USER_LOGIN_API);

                getUserProfileInfo(outhToken);

                JSONObject userObject=new JSONObject();
                try {
                    userObject.put("name",profileName);
                    userObject.put("phNumber",mPhoneNumber);
                    userObject.put("regID",regID);
                    msg = postUserInfo(userObject,outhToken);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
                return msg;
            }

            @Override
            protected void onPostExecute(String msg) {
                Log.i(TAG, msg);
            }
        }.execute(null, null, null);
    }

    private String postUserInfo(JSONObject userObject, String outhToken){
        String msg="";
        HttpClient httpClient = new DefaultHttpClient();
        // replace with your url
        HttpPost httpPost = new HttpPost(USER_LOGIN_API);
        httpPost.setHeader("Authorization","Bearer "+outhToken);

        StringEntity se;

        try {
            se = new StringEntity(userObject.toString());
            se.setContentType(new BasicHeader(HTTP.CONTENT_TYPE,"application/json"));
            httpPost.setEntity(se);

            HttpResponse response = httpClient.execute(httpPost);
            // write response to log
            Log.d("Http Post Response:", response.getStatusLine().toString());
        } catch (ClientProtocolException | UnsupportedEncodingException e) {
            // Log exception
            e.printStackTrace();
        } catch (IOException e) {
            // Log exception
            e.printStackTrace();
        }
        return msg;
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


    /*
        OAuth Login code begins here
     */

    public void onLoginClicked(View view){
        String token=getOAuthToken(context);
        if(token.isEmpty())
            pickUserAccount();
        else
            Toast.makeText(context,"Already registered through OAuth",Toast.LENGTH_LONG).show();
    }

    /**
     * Gets the current OAuth token for application.
     * <p>
     * If result is empty, the app needs to register.
     *
     * @return OAuth token, or empty string if there is no existing
     *         OAuth token.
     */
    private String getOAuthToken(Context context) {
        final SharedPreferences prefs = getLoginPreferences(context);
        String OAuthToken = prefs.getString(PROPERTY_OAUTH_TOKEN, "");
        if (OAuthToken.isEmpty()) {
            Log.i(TAG, "OAuth not found.");
            return "";
        }
        return OAuthToken;
    }

    private void pickUserAccount() {
        String[] accountTypes = new String[]{"com.google","in.ac.iiitd"};
        Intent intent = AccountPicker.newChooseAccountIntent(null, null,
                accountTypes, false, null, null, null, null);
        startActivityForResult(intent, REQUEST_CODE_PICK_ACCOUNT);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQUEST_CODE_PICK_ACCOUNT) {
            // Receiving a result from the AccountPicker
            if (resultCode == RESULT_OK) {
                mEmail = data.getStringExtra(AccountManager.KEY_ACCOUNT_NAME);
                // With the account name acquired, go get the auth token
                Log.i(TAG,"Username: "+mEmail);
                getUsername();
            } else if (resultCode == RESULT_CANCELED) {
                // The account picker dialog closed without selecting an account.
                // Notify users that they must pick an account to proceed.
                Toast.makeText(this, R.string.pick_account, Toast.LENGTH_SHORT).show();
            }
        }
    }

    /**
     * Attempts to retrieve the username.
     * If the account is not yet known, invoke the picker. Once the account is known,
     * start an instance of the AsyncTask to get the auth token and do work with it.
     */
    public void getUsername(){

        if (mEmail == null) {
            pickUserAccount();
        } else {
            if (isDeviceOnline()) {
                new GetUsernameTask(this, mEmail, SCOPE).execute();
            } else {
                Toast.makeText(this, R.string.not_connected, Toast.LENGTH_LONG).show();
            }
        }
    }

    public boolean isDeviceOnline(){
        ConnectivityManager conMgr = (ConnectivityManager)getSystemService(Context.CONNECTIVITY_SERVICE);

        //Check network availability
        if(conMgr.getActiveNetworkInfo()==null)
            return false;

        return true;
    }

    /**
     * Stores the OAuth token in the application's
     * {@code SharedPreferences}.
     *
     * @param context application's context.
     * @param token OAuth token
     */
    private void storeOAuthToken(Context context, String token) {
        final SharedPreferences prefs = getLoginPreferences(context);
        Log.i(TAG, "Saving token " + token);
        SharedPreferences.Editor editor = prefs.edit();
        editor.putString(PROPERTY_OAUTH_TOKEN, token);
        editor.commit();
    }

    private void getUserProfileInfo(String outhToken){
        HttpClient Client = new DefaultHttpClient();

        String URL = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token="+outhToken;
        try
        {
            String SetServerString = "";

            // Create Request to server and get response

            HttpGet httpget = new HttpGet(URL);
            ResponseHandler<String> responseHandler = new BasicResponseHandler();
            SetServerString = Client.execute(httpget, responseHandler);

            // Show response on activity

            Log.v("Response: ",SetServerString);

            JSONObject profileInfo=new JSONObject(SetServerString);
            profileName=profileInfo.getString("name");
        }
        catch(Exception ex)
        {
            ex.printStackTrace();
        }
    }


    public class GetUsernameTask extends AsyncTask<Void,Void,Void> {
        Activity mActivity;
        String mScope;
        String mEmail;

        GetUsernameTask(Activity activity, String name, String scope) {
            this.mActivity = activity;
            this.mScope = scope;
            this.mEmail = name;
        }

        /**
         * Executes the asynchronous job. This runs when you call execute()
         * on the AsyncTask instance.
         */
        @Override
        protected Void doInBackground(Void... params) {
            try {
                String token = fetchToken();
                if (token != null) {
                    // Insert the good stuff here.
                    // Use the token to access the user's Google data.
                    Log.v(TAG,"Token received: "+token);
                    storeOAuthToken(context,token);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
            return null;
        }

        /**
         * Gets an authentication token from Google and handles any
         * GoogleAuthException that may occur.
         */
        protected String fetchToken() throws IOException {
            try {
                return GoogleAuthUtil.getToken(mActivity, mEmail, mScope);
            } catch (UserRecoverableAuthException userRecoverableException) {
                // GooglePlayServices.apk is either old, disabled, or not present
                // so we need to show the user some UI in the activity to recover.
                handleException(userRecoverableException);
            } catch (GoogleAuthException fatalException) {
                // Some other type of unrecoverable exception has occurred.
                // Report and log the error as appropriate for your app.
                fatalException.printStackTrace();
            }
            return null;
        }

        @Override
        protected void onPostExecute(Void result){
            sendRegistrationIdToBackend();
        }

    }

    /**
     * This method is a hook for background threads and async tasks that need to
     * provide the user a response UI when an exception occurs.
     */
    public void handleException(final Exception e) {
        // Because this call comes from the AsyncTask, we must ensure that the following
        // code instead executes on the UI thread.
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (e instanceof GooglePlayServicesAvailabilityException) {
                    // The Google Play services APK is old, disabled, or not present.
                    // Show a dialog created by Google Play services that allows
                    // the user to update the APK
                    int statusCode = ((GooglePlayServicesAvailabilityException)e)
                            .getConnectionStatusCode();
                    Dialog dialog = GooglePlayServicesUtil.getErrorDialog(statusCode,
                            LoginActivity.this,
                            REQUEST_CODE_RECOVER_FROM_PLAY_SERVICES_ERROR);
                    dialog.show();
                } else if (e instanceof UserRecoverableAuthException) {
                    // Unable to authenticate, such as when the user has not yet granted
                    // the app access to the account, but the user can fix this.
                    // Forward the user to an activity in Google Play services.
                    Intent intent = ((UserRecoverableAuthException)e).getIntent();
                    startActivityForResult(intent,
                            REQUEST_CODE_RECOVER_FROM_PLAY_SERVICES_ERROR);
                }
            }
        });
    }
}
