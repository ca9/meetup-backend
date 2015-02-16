package iiitd.ac.in.dsys.meetup;

import android.accounts.AccountManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.Toast;

import com.appspot.intense_terra_821.users_api.UsersApi;
import com.appspot.intense_terra_821.users_api.UsersApiRequest;
import com.appspot.intense_terra_821.users_api.UsersApiRequestInitializer;
import com.google.android.gms.common.api.GoogleApiClient;
import com.google.api.client.extensions.android.http.AndroidHttp;
import com.google.api.client.googleapis.extensions.android.gms.auth.GoogleAccountCredential;
import com.google.api.client.http.HttpHeaders;
import com.google.api.client.json.gson.GsonFactory;

import java.util.Arrays;
import java.util.Collection;

import iiitd.ac.in.dsys.meetup.messages.firstLoginTask;
import iiitd.ac.in.dsys.meetup.messages.pingHelloTask;


public class MainActivity extends ActionBarActivity {

    private SharedPreferences settings;

    // Services
    UsersApi usersApiInst;

    // Credentials, client ID, Authorization
    GoogleAccountCredential credential;
    private String accountEmail;
    private static final int REQUEST_ACCOUNT_PICKER = 2;
    public static final String WEB_CLIENT_ID = "812458715891-p8e6e4oqph65matkdr1v06r02vtri1du.apps.googleusercontent.com";
    // Unused
    public static final String ANDROID_CLIENT_ID = "812458715891-cd592i6lgul160gf15ma2tbb1oj4k4k2.apps.googleusercontent.com";
    /* Client used to interact with Google APIs. */



    // Scopes
    public static final String EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email";
    public static final String CONTACTS_SCOPE = "https://www.googleapis.com/auth/contacts.readonly";
    public static final Collection<String> SCOPES = Arrays.asList(EMAIL_SCOPE, CONTACTS_SCOPE);



    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // fetch settings
        settings = getSharedPreferences("MeetupPreferences", 0);
        // set Credentials (Pick chosen Account)
        setCredentials();
        // build services
        buildApiServices(false, "192.168.1.6");

    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
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
        credential.setSelectedAccountName(settings.getString("ACCOUNT_NAME", null));
        if (credential.getSelectedAccountName() != null) {
            // Already signed in, begin app!
            Toast.makeText(getBaseContext(), "Logged in with : " + credential.getSelectedAccountName(), Toast.LENGTH_SHORT).show();
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
