package iiitd.ac.in.dsys.meetup.messages;

import android.app.Activity;
import android.content.Context;
import android.os.AsyncTask;
import android.util.Log;
import android.widget.Toast;

import com.appspot.intense_terra_821.users_api.UsersApi;
import com.appspot.intense_terra_821.users_api.model.ApiAuthenticationFirstLoginMessage;
import com.appspot.intense_terra_821.users_api.model.ApiCommonApiReply;
import com.google.android.gms.auth.GoogleAuthException;
import com.google.android.gms.auth.GoogleAuthUtil;

import java.io.IOException;

/**
 * Created by aditya on 14/02/15.
 */
public class firstLoginTask extends AsyncTask<Void, Void, ApiCommonApiReply> {
    Context context;
    UsersApi usersApi;
    ApiAuthenticationFirstLoginMessage firstLoginMessage;
    String TAG="MainActivity";

    public firstLoginTask(Context context, UsersApi usersApi, String fullName, String phNumber, String regID) {
        this(context, usersApi,
                new ApiAuthenticationFirstLoginMessage().setRegID(regID).setName(fullName).setPhNumber(phNumber));
    }

    public firstLoginTask(Context context, UsersApi usersApi, ApiAuthenticationFirstLoginMessage firstLoginMessage) {
        this.context = context;
        this.usersApi = usersApi;
        this.firstLoginMessage = firstLoginMessage;
    }

    @Override
    protected ApiCommonApiReply doInBackground(Void... params) {
        ApiCommonApiReply reply = null;
        try {
            UsersApi.FirstLogin aRequest = usersApi.firstLogin(firstLoginMessage);
            aRequest.execute();
        } catch (IOException e) {
            Log.d(TAG, e.getMessage(), e);
            e.printStackTrace();
        }
        return reply;
    }

    @Override
    protected void onPostExecute(ApiCommonApiReply reply) {
        if (reply != null)
            Toast.makeText(context, reply.getStrValue(), Toast.LENGTH_LONG).show();
    }

    public void addTokenToMessage(String token) {
        firstLoginMessage.setShortLivedAuthorizationToken(token);
    }

}
