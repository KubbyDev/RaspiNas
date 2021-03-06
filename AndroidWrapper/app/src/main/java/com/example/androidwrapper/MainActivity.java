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
import android.widget.TextView;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;

public class MainActivity extends AppCompatActivity {

    private static final int STORAGE_PERMISSION_CODE = 101;
    private static final String NAME_PREFIX = "RaspiNas ";
    private String localDir = null;
    private String logsFile = null;
    private TextView mainTextView = null;
    private boolean syncDone = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Gets an external pictures directory
        File locDir = getExternalFilesDir("LocalDirectory");
        if (locDir == null) return;
        localDir = locDir.getAbsolutePath();

        // Gets the directory for the logs file
        File logsDir = getExternalFilesDir(null);
        if (logsDir == null) return;
        logsFile = logsDir.getAbsolutePath() + "/logs.txt";

        // Finds the main text view
        mainTextView = findViewById(R.id.textView);

        // Starts reading the logs on another thread
        new Thread() {
            @Override
            public void run() {
                while (true) {

                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            String res = runCommand("tail -n 100 " + logsFile);
                            mainTextView.setText(res);
                        }
                    });

                    try { Thread.sleep(100); } catch (InterruptedException e) { e.printStackTrace(); }
                }
            }
        }.start();

        syncDone = false;
        // Starts the synchronisation on another thread
        new Thread() {
            @Override
            public void run() {
                synchronise();
                syncDone = true;
            }
        }.start();

        // Lauches the rest of the app asynchronously because it seems like the onCreate function
        // Needs to return for the textView to update properly
        new Thread() {
            @Override
            public void run() {

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

                    closeApp();
                }
            }
        }.start();
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
        else
            waitForSync();

        // Closes the app
        closeApp();
    }

    // BLOCKING: waits for the synchronisation to finish
    private void waitForSync() {
        while(!syncDone)
            try { Thread.sleep(500); } catch (InterruptedException e) { e.printStackTrace(); }
    }

    private void closeApp() {
        try { Thread.sleep(2000); } catch (InterruptedException e) { e.printStackTrace(); }
        finish();
        System.exit(0);
    }

    // Synchronises the local folder with the server (calls the python client)
    private void synchronise() {

        // Starts a python instance
        if (!Python.isStarted())
            Python.start(new AndroidPlatform(this));

        // Launches the python client with that directory as local directory
        PyObject script = Python.getInstance().getModule("main");
        try {
            script.callAttr("launch", localDir, logsFile);
        } catch(Exception e) {
            try { Thread.sleep(2000); } catch (InterruptedException ex) { ex.printStackTrace(); }
            e.printStackTrace();
            closeApp();
        }
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
        for(File image : new File(localDir).listFiles()) {
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

    // https://stackoverflow.com/questions/23608005/execute-shell-commands-and-get-output-in-a-textview
    private String runCommand(String cmd)
    {
        String o = "";
        try {
            Process p = Runtime.getRuntime().exec(cmd);
            BufferedReader b = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while((line = b.readLine()) != null)
                o += line + "\n";
        } catch(Exception e) { o="error"; }
        return o;
    }
}
