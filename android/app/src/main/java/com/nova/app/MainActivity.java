package com.nova.app;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.PermissionRequest;
import android.widget.TextView;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends Activity {
    private static final int AUDIO_PERMISSION_REQUEST = 1001;
    private PermissionRequest pendingAudioRequest;

    private boolean isTrustedAudioRequest(PermissionRequest request) {
        if (request == null) return false;
        Uri origin = request.getOrigin();
        String[] resources = request.getResources();

        return origin != null
            && "http".equalsIgnoreCase(origin.getScheme())
            && "127.0.0.1".equals(origin.getHost())
            && origin.getPort() == 8765
            && resources != null
            && resources.length == 1
            && PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resources[0]);
    }

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
            view.setWebChromeClient(new WebChromeClient() {
                @Override
                public void onPermissionRequest(PermissionRequest request) {
                    runOnUiThread(() -> {
                        if (!isTrustedAudioRequest(request)) {
                            request.deny();
                            return;
                        }

                        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                                == PackageManager.PERMISSION_GRANTED) {
                            request.grant(new String[]{
                                PermissionRequest.RESOURCE_AUDIO_CAPTURE
                            });
                        } else {
                            if (pendingAudioRequest != null) {
                                pendingAudioRequest.deny();
                            }
                            pendingAudioRequest = request;
                            requestPermissions(
                                new String[]{Manifest.permission.RECORD_AUDIO},
                                AUDIO_PERMISSION_REQUEST
                            );
                        }
                    });
                }

                @Override
                public void onPermissionRequestCanceled(PermissionRequest request) {
                    if (pendingAudioRequest == request) {
                        pendingAudioRequest = null;
                    }
                }
            });

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
    public void onRequestPermissionsResult(
            int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == AUDIO_PERMISSION_REQUEST) {
            PermissionRequest request = pendingAudioRequest;
            pendingAudioRequest = null;

            if (request == null) return;

            if (grantResults.length > 0
                    && grantResults[0] == PackageManager.PERMISSION_GRANTED
                    && isTrustedAudioRequest(request)) {
                request.grant(new String[]{
                    PermissionRequest.RESOURCE_AUDIO_CAPTURE
                });
            } else {
                request.deny();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (pendingAudioRequest != null) {
            pendingAudioRequest.deny();
            pendingAudioRequest = null;
        }

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
