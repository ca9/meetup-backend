package iiitd.ac.in.dsys.meetup.messages;

import android.content.Context;
import android.os.AsyncTask;
import android.util.Log;
import android.widget.Toast;

import com.appspot.intense_terra_821.users_api.UsersApi;
import com.appspot.intense_terra_821.users_api.model.ApiAuthenticationFirstLoginMessage;
import com.appspot.intense_terra_821.users_api.model.ApiCommonApiReply;

import java.io.IOException;

/**
 * Created by aditya on 14/02/15.
 */
public class firstLoginTask extends AsyncTask<Void, Void, ApiCommonApiReply> {
    Context context;
    UsersApi usersApi;
    ApiAuthenticationFirstLoginMessage firstLoginMessage;

    public firstLoginTask(Context c, UsersApi usersApi, String regID, String fullName, String phNumber) {
        this(c, usersApi,
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
            Log.d("Meetup", e.getMessage(), e);
            e.printStackTrace();
        }
        return reply;
    }

    @Override
    protected void onPostExecute(ApiCommonApiReply reply) {
        if (reply != null)
            Toast.makeText(context, reply.getStrValue(), Toast.LENGTH_LONG).show();
    }
}