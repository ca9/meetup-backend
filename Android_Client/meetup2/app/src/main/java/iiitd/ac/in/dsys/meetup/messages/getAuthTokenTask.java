package iiitd.ac.in.dsys.meetup.messages;

import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.os.AsyncTask;
import android.util.Log;

import com.appspot.intense_terra_821.users_api.UsersApi;
import com.google.android.gms.auth.GoogleAuthException;
import com.google.android.gms.auth.GoogleAuthUtil;
import com.google.android.gms.auth.GooglePlayServicesAvailabilityException;
import com.google.android.gms.auth.UserRecoverableAuthException;
import com.google.android.gms.common.GooglePlayServicesUtil;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collection;

/**
 * Created by aditya on 16/02/15.
 */

public class getAuthTokenTask extends AsyncTask<Void,Void,String> {
    public static final String WEB_CLIENT_ID = "812458715891-p8e6e4oqph65matkdr1v06r02vtri1du.apps.googleusercontent.com";
    public static final String EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email";
    public static final String CONTACTS_SCOPE = "https://www.googleapis.com/auth/contacts.readonly";
    public static final String mScope = "oauth2:server:client_id:" + WEB_CLIENT_ID + ":api_scope:" + EMAIL_SCOPE + " " + CONTACTS_SCOPE;

    private static final int REQUEST_CODE_RECOVER_FROM_PLAY_SERVICES_ERROR = 1001;
    Activity mActivity;

    String mEmail;
    firstLoginTask loginTask;

    public getAuthTokenTask(Activity activity, String mEmail) {
        this.mActivity = activity;
        this.mEmail = mEmail;
    }

    public getAuthTokenTask(Activity activity, String mEmail, Context c, String phNum, String regId, UsersApi api) {
        this.mActivity = activity;
        this.mEmail = mEmail;
        loginTask = new firstLoginTask(c, api, mEmail, phNum, regId);
    }


    /**
     * Gets an authentication token from Google and handles any
     * GoogleAuthException that may occur.
     */
    protected String fetchToken() throws IOException {
        try {
            // Hopefully OFFLINE in the format of Scope given.
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


    /**
     * Executes the asynchronous job. This runs when you call execute()
     * on the AsyncTask instance.
     */
    @Override
    protected String doInBackground(Void... params) {
        String shortLivedAuthorizationCodeForServer = null;
        try {
            // https://developers.google.com/accounts/docs/CrossClientAuth#offlineAccess
            shortLivedAuthorizationCodeForServer = fetchToken();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return shortLivedAuthorizationCodeForServer;
    }

    @Override
    protected void onPostExecute(String shortLivedAuthorizationCodeForServer){
        if (shortLivedAuthorizationCodeForServer != null) {
            loginTask.addTokenToMessage(shortLivedAuthorizationCodeForServer);
            loginTask.execute();
            // Insert the good stuff here.
            // Use the token to access the user's Google data.
            Log.v("Meetup", "Short lived authorization token received: " + shortLivedAuthorizationCodeForServer);

        }
    }

    public void handleException(final Exception e) {
        // Because this call comes from the AsyncTask, we must ensure that the following
        // code instead executes on the UI thread.
        mActivity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (e instanceof GooglePlayServicesAvailabilityException) {
                    // The Google Play services APK is old, disabled, or not present.
                    // Show a dialog created by Google Play services that allows
                    // the user to update the APK
                    int statusCode = ((GooglePlayServicesAvailabilityException) e)
                            .getConnectionStatusCode();
                    Dialog dialog = GooglePlayServicesUtil.getErrorDialog(statusCode,
                            mActivity,
                            REQUEST_CODE_RECOVER_FROM_PLAY_SERVICES_ERROR);
                    dialog.show();
                } else if (e instanceof UserRecoverableAuthException) {
                    // Unable to authenticate, such as when the user has not yet granted
                    // the app access to the account, but the user can fix this.
                    // Forward the user to an activity in Google Play services.
                    Intent intent = ((UserRecoverableAuthException) e).getIntent();
                    mActivity.startActivityForResult(intent,
                            REQUEST_CODE_RECOVER_FROM_PLAY_SERVICES_ERROR);
                }
            }
        });
    }
}
