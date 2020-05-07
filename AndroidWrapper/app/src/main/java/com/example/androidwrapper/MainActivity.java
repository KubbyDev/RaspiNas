package com.example.androidwrapper;

import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;

import android.annotation.SuppressLint;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Log;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.File;
import java.io.IOException;
import java.io.OutputStream;

public class MainActivity extends AppCompatActivity {

    @SuppressLint("WrongThread") // Could be useful to do it on worker thread one day, but for now fuck it
    @Override
    protected void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Starts a python instance
        if (!Python.isStarted())
            Python.start(new AndroidPlatform(this));

        // Gets an external pictures directory
        File localDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        if(localDir == null) return;

        // Gets the directory for the logs file
        File logsDir = getExternalFilesDir(null);
        if(logsDir == null) return;

        // Launches the python client with that directory as local directory
        PyObject script = Python.getInstance().getModule("main");
        script.callAttr("launch", localDir.toString(), logsDir.toString());

        // Removes all the images in the galery
        final ContentResolver resolver = this.getContentResolver();
        resolver.delete(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, null, null);

        // Copies the images from the python local_dir to the galery
        for(File image : localDir.listFiles()) {
            Log.d("GALLERY: ", "Adding " + image + " to the gallery");

            // Inserts a database entry with name and mime type
            final ContentValues  contentValues = new ContentValues();
            contentValues.put(MediaStore.MediaColumns.DISPLAY_NAME, image.getName());
            contentValues.put(MediaStore.MediaColumns.MIME_TYPE,
                    "image/"+image.getName().substring(image.getName().lastIndexOf('.')+1));
            Uri uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, contentValues);

            // Adds the image itself
            try {
                Bitmap bitmap = BitmapFactory.decodeFile(image.getAbsolutePath());
                OutputStream stream = resolver.openOutputStream(uri);
                if(bitmap != null) bitmap.compress(Bitmap.CompressFormat.JPEG, 95, stream);
                stream.close();
            } catch (IOException e) { e.printStackTrace(); }
        }

        // Closes the app
        finish();
        System.exit(0);
    }
}
