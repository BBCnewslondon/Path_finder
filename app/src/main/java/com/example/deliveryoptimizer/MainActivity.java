package com.example.deliveryoptimizer;

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {

    private EditText addressesInput;
    private Spinner algorithmSpinner;
    private Spinner optimizeBySpinner;
    private Button generateRouteButton;
    private ProgressBar progressBar;
    private TextView resultsSummary;
    private TextView resultsOutput;
    private WebView mapWebView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        addressesInput = findViewById(R.id.addresses_input);
        algorithmSpinner = findViewById(R.id.algorithm_spinner);
        optimizeBySpinner = findViewById(R.id.optimize_by_spinner);
        generateRouteButton = findViewById(R.id.generate_route_button);
        progressBar = findViewById(R.id.progress_bar);
        resultsSummary = findViewById(R.id.results_summary);
        resultsOutput = findViewById(R.id.results_output);
        mapWebView = findViewById(R.id.map_webview);

        mapWebView.getSettings().setJavaScriptEnabled(true);
        mapWebView.getSettings().setDomStorageEnabled(true);


        // Populate spinners
        ArrayAdapter<CharSequence> algorithmAdapter = ArrayAdapter.createFromResource(this,
                R.array.algorithm_options, android.R.layout.simple_spinner_item);
        algorithmAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        algorithmSpinner.setAdapter(algorithmAdapter);

        ArrayAdapter<CharSequence> optimizeByAdapter = ArrayAdapter.createFromResource(this,
                R.array.optimize_by_options, android.R.layout.simple_spinner_item);
        optimizeByAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        optimizeBySpinner.setAdapter(optimizeByAdapter);

        generateRouteButton.setOnClickListener(v -> generateRoute());
    }

    private void generateRoute() {
        String addresses = addressesInput.getText().toString();
        if (addresses.trim().isEmpty()) {
            Toast.makeText(this, "Please enter at least two addresses", Toast.LENGTH_SHORT).show();
            return;
        }

        String algorithm = algorithmSpinner.getSelectedItem().toString();
        String optimizeBy = optimizeBySpinner.getSelectedItem().toString();

        progressBar.setVisibility(View.VISIBLE);
        resultsOutput.setText("");
        resultsSummary.setText("");

        // Run Python code in a background thread
        new Thread(() -> {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(this));
            }
            Python py = Python.getInstance();
            PyObject androidMain = py.getModule("android_main");

            String appHome = getFilesDir().getAbsolutePath();

            PyObject result = androidMain.callAttr("run_optimization", addresses, algorithm, optimizeBy, true, appHome);

            runOnUiThread(() -> {
                progressBar.setVisibility(View.GONE);
                if (result.get("error") != null) {
                    resultsSummary.setText("Error");
                    resultsOutput.setText(result.get("error").toString());
                } else {
                    String totalCost = result.get("total_cost").toString();
                    String costUnit = result.get("cost_unit").toString();
                    resultsSummary.setText("Total " + optimizeBy + ": " + totalCost + " " + costUnit);

                    PyObject orderedAddresses = result.get("ordered_addresses");
                    StringBuilder routeStr = new StringBuilder();
                    for (PyObject item : orderedAddresses.asList()) {
                        routeStr.append(item.toString()).append("\n");
                    }
                    resultsOutput.setText(routeStr.toString());

                    String mapPath = "file://" + result.get("map_path").toString();
                    mapWebView.loadUrl(mapPath);
                }
            });
        }).start();
    }
}
