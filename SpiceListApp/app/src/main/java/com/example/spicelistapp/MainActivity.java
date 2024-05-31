package com.example.spicelistapp;

import androidx.activity.EdgeToEdge;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;

import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {
    private RecyclerView recyclerView;
    private SpicePositionAdapter itemAdapter;
    private List<SpicePosition> spiceList;
    private Button refreshButton;
    private DatabaseReference databaseReference;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main_view), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        recyclerView = findViewById(R.id.recyclerView);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));

        spiceList = new ArrayList<>();
        itemAdapter = new SpicePositionAdapter(spiceList);
        recyclerView.setAdapter(itemAdapter);

        refreshButton = findViewById(R.id.refreshButton);
        databaseReference = FirebaseDatabase.getInstance().getReference("");

        // Fetch data when the app is opened
        fetchData();

        // Set onClickListener to the refresh button
        refreshButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                fetchData();
            }
        });
    }

    private void fetchData() {
        databaseReference.addListenerForSingleValueEvent(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot dataSnapshot) {
                spiceList.clear();
                for (DataSnapshot snapshot : dataSnapshot.getChildren()) {
                    int pos;
                    try {
                        pos = Integer.parseInt(snapshot.getKey());
                    }
                    catch (NumberFormatException e) {
                        continue;
                    }
                    String name = snapshot.getValue(String.class);
                    SpicePosition spicePosition = new SpicePosition(pos, name);
                    spiceList.add(spicePosition);
                }
                itemAdapter.notifyDataSetChanged();
            }

            @Override
            public void onCancelled(@NonNull DatabaseError databaseError) {
                // Handle possible errors.
            }
        });

    }
}