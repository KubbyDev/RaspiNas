package com.example.androidwrapper;

import androidx.appcompat.app.AppCompatActivity;

import android.os.Bundle;
import android.os.Environment;
import android.util.Log;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        new Thread() {
            @Override
            public void run() {
                // Gets an external pictures directory
                String dir = getExternalFilesDir(Environment.DIRECTORY_PICTURES).toString();
                Log.d("DIRECTORY: ", dir);
                // Launches the python client with that directory as local directory
                PyObject script = Python.getInstance().getModule("main");
                PyObject res = script.callAttr("launch", dir);
            }
        }.start();
    }
}
