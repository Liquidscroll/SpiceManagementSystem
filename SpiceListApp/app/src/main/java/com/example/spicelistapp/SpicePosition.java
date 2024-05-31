package com.example.spicelistapp;

public class SpicePosition
{
    private int position;
    private String spiceName;
    public SpicePosition() {}
    public SpicePosition(int position, String spiceName)
    {
        this.position = position;
        this.spiceName = spiceName;
    }

    public int getPosition()
    {
        return position;
    }

    public String getName()
    {
        return spiceName;
    }
}
