package iiitd.ac.in.dsys.meetup.messages;

import android.content.Context;
import android.os.AsyncTask;
import android.util.Log;

import com.appspot.intense_terra_821.users_api.UsersApi;

import java.io.IOException;

/**
 * Created by aditya on 16/02/15.
 */
public class contactsTask extends AsyncTask<Void, Void, Void> {
    Context context;
    UsersApi usersApi;

    public contactsTask(Context context, UsersApi usersApi) {
        this.context = context;
//        this.builder = builder;
        this.usersApi = usersApi;
    }

    @Override
    protected Void doInBackground(Void... params) {
        try {
            usersApi.printContacts().execute();
        } catch (IOException e) {
            Log.d("Meetup", e.getMessage(), e);
            e.printStackTrace();
        }
        return null;
    }
}
