package com.nova.app;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.widget.TextView;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(this));
            }
            Python.getInstance()
                .getModule("android_bootstrap")
                .callAttr("start", getFilesDir().getAbsolutePath());

            WebView view = new WebView(this);
            WebSettings settings = view.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setDomStorageEnabled(true);
            view.setWebViewClient(new WebViewClient());
            view.setWebChromeClient(new WebChromeClient());
            setContentView(view);
            view.postDelayed(
                () -> view.loadUrl("http://127.0.0.1:8765"), 500
            );
        } catch (Exception error) {
            TextView message = new TextView(this);
            message.setText("NOVA startup error: " + error);
            setContentView(message);
        }
    }

    @Override
    protected void onDestroy() {
        try {
            if (Python.isStarted()) {
                Python.getInstance()
                    .getModule("android_bootstrap")
                    .callAttr("stop");
            }
        } catch (Exception ignored) {
        }
        super.onDestroy();
    }
}
