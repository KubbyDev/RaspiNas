package com.example.androidwrapper;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import android.Manifest;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.util.Log;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.OutputStream;

public class MainActivity extends AppCompatActivity {

    private static final int STORAGE_PERMISSION_CODE = 101;
    private static final String NAME_PREFIX = "RaspiNas ";
    private File localDir = null;
    private boolean syncDone = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        syncDone = false;
        // Starts the synchronisation on another thread
        new Thread() {
            @Override
            public void run() {
                synchronise();
                syncDone = true;
            }
        }.start();

        // Checks if the write permission is given
        if (ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                == PackageManager.PERMISSION_DENIED) {

            // If it is not given, requests it
            ActivityCompat.requestPermissions(MainActivity.this,
                    new String[] { Manifest.permission.WRITE_EXTERNAL_STORAGE },
                    STORAGE_PERMISSION_CODE);
        }
        else {
            // If it is given, wait for the synchronisation to finish and updates the gallery
            waitForSync();
            updateGallery();
            // Closes the app
            finish();
            System.exit(0);
        }
    }

    // When the write permission is given
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            // Wait for the synchronisation to finish and updates the gallery
            waitForSync();
            updateGallery();
        }

        // Closes the app
        finish();
        System.exit(0);
    }

    // BLOCKING: waits for the synchronisation to finish
    private void waitForSync() {
        while(!syncDone)
            try { Thread.sleep(500); } catch (InterruptedException e) { e.printStackTrace(); }
    }

    // Synchronises the local folder with the server (calls the python client)
    private void synchronise() {

        // Starts a python instance
        if (!Python.isStarted())
            Python.start(new AndroidPlatform(this));

        // Gets an external pictures directory
        localDir = getExternalFilesDir("LocalDirectory");
        if(localDir == null) return;

        // Gets the directory for the logs file
        File logsDir = getExternalFilesDir(null);
        if(logsDir == null) return;

        // Launches the python client with that directory as local directory
        PyObject script = Python.getInstance().getModule("main");
        script.callAttr("launch", localDir.toString(), logsDir.toString());
    }

    // Copies the files in the local folder to the gallery
    private void updateGallery() {

        // Removes all the images in the galery
        final ContentResolver resolver = this.getContentResolver();
        resolver.delete(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                MediaStore.MediaColumns.DISPLAY_NAME + " LIKE ?", new String[] { NAME_PREFIX + "%" });
        resolver.delete(MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
                MediaStore.MediaColumns.DISPLAY_NAME + " LIKE ?", new String[] { NAME_PREFIX + "%" });

        // Copies the images from the python local_dir to the galery
        for(File image : localDir.listFiles()) {
            Log.d("GALLERY: ", "Adding " + image + " to the gallery");

            // Inserts a database entry with name and mime type
            final ContentValues contentValues = new ContentValues();
            String mime = getMime(image.getName());
            contentValues.put(MediaStore.MediaColumns.DISPLAY_NAME, NAME_PREFIX + image.getName());
            contentValues.put(MediaStore.MediaColumns.TITLE, image.getName());
            contentValues.put(MediaStore.MediaColumns.MIME_TYPE, mime);
            Uri folder = MediaStore.Images.Media.EXTERNAL_CONTENT_URI;
            if (mime.startsWith("video")) folder = MediaStore.Video.Media.EXTERNAL_CONTENT_URI;
            Uri uri = resolver.insert(folder, contentValues);

            // Adds the image itself
            try (FileInputStream fis = new FileInputStream(image.getAbsolutePath());
                 OutputStream os = resolver.openOutputStream(uri)) {
                byte[] buf = new byte[1024];
                int len;
                while ((len = fis.read(buf)) > 0)
                    os.write(buf, 0, len);
            } catch (IOException e) { e.printStackTrace(); }
        }
    }

    private String getMime(String filename) {
        String ext = filename.substring(filename.lastIndexOf('.')+1);
        if(ext.equalsIgnoreCase("mp4")) return "video/mp4";
        if(ext.equalsIgnoreCase("jpg")) return "image/jpeg";
        return "image/" + ext.toLowerCase();
    }
}
