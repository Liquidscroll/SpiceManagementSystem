package com.example.spicelistapp;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;
import java.util.Locale;

public class SpicePositionAdapter extends RecyclerView.Adapter<SpicePositionAdapter.ItemViewHolder>
{
    private List<SpicePosition> spicePositionList;
    public SpicePositionAdapter(List<SpicePosition> spiceList)
    {
        this.spicePositionList = spiceList;
    }

    @NonNull
    @Override
    public ItemViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_view, parent, false);
        return new ItemViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ItemViewHolder holder, int position) {
        SpicePosition item = spicePositionList.get(position);
        holder.posNumber.setText(String.format(Locale.getDefault(), "Postition %d: ",item.getPosition()));
        holder.spiceName.setText(item.getName());
    }

    @Override
    public int getItemCount() {
        return spicePositionList.size();
    }

    public static class ItemViewHolder extends RecyclerView.ViewHolder {
        TextView posNumber;
        TextView spiceName;

        public ItemViewHolder(@NonNull View itemView) {
            super(itemView);
            posNumber = itemView.findViewById(R.id.nameTextView);
            spiceName = itemView.findViewById(R.id.descriptionTextView);
        }
    }

}
