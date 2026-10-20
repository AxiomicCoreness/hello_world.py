package com.fruitfly.games.rhythm.web;

/**
 * Stage colour sets. LIGHT is the default: an off-white backdrop (#f7f6f3)
 * with a thin light-grey perspective floor converging to a vanishing point
 * at mid-height, drawn procedurally (style reference only, no image), and
 * dark text. AR is the dimmed AR-photo / camera backdrop (?bg=ar, ?camera=1).
 */
final class Theme {
    final boolean light;
    final String backdrop;
    final String dim;
    final String floorLine;
    final String laneEven;
    final String laneOdd;
    final String laneFlash;
    final String hitLine;
    final String[] notes;
    final String laneKey;
    final String laneLabel;
    final String gridMajor;
    final String gridMinor;
    final String origin;
    final String originStand;
    final String regionFill;
    final String regionFillLabelOnly;
    final String regionText;
    final String regionTextLabelOnly;
    final String neuron;
    final String neuronHot;
    final String excitIdle;
    final String inhibIdle;
    final String excitFlashRgb;
    final String inhibFlashRgb;
    final String caption;
    final String hudText;
    final String bodyClass;
    final String tileFill;
    final String tileEdge;
    final String flyBody;
    final String flyLine;
    final String[] saberCore;
    final String[] saberGlow;
    final String blockRgb;
    final String flashRgb;
    final String leader;

    private Theme(boolean light) {
        this.light = light;
        if (light) {
            backdrop = "#f7f6f3";
            dim = null;
            floorLine = "rgba(40,40,40,0.13)";
            laneEven = "rgba(30,34,48,0.035)";
            laneOdd = "rgba(30,34,48,0.065)";
            laneFlash = "rgba(40,90,210,0.16)";
            hitLine = "#2b2f3a";
            notes = new String[] {"#d81b4f", "#1f6fd1", "#d81b4f", "#1f6fd1"};
            laneKey = "#1d2230";
            laneLabel = "#4a5165";
            gridMajor = "rgba(40,40,40,0.20)";
            gridMinor = "rgba(40,40,40,0.09)";
            origin = "rgba(160,110,0,0.9)";
            originStand = "rgba(160,110,0,0.4)";
            regionFill = "rgba(50,90,170,0.12)";
            regionFillLabelOnly = "rgba(90,95,110,0.08)";
            regionText = "#22293b";
            regionTextLabelOnly = "#7a8094";
            neuron = "#2f6fd6";
            neuronHot = "#0a9b63";
            excitIdle = "rgba(40,90,180,0.32)";
            inhibIdle = "rgba(200,40,70,0.22)";
            excitFlashRgb = "0,155,95";
            inhibFlashRgb = "215,30,60";
            caption = "#a8520a";
            hudText = "#1d2230";
            bodyClass = "theme-light";
            tileFill = "rgba(40,90,200,0.07)";
            tileEdge = "rgba(40,60,110,0.45)";
            flyBody = "rgba(40,44,58,0.85)";
            flyLine = "rgba(40,44,58,0.7)";
            saberCore = new String[] {"#c2153f", "#1a5fc0"};
            saberGlow = new String[] {"rgba(216,27,79,0.22)", "rgba(31,111,209,0.22)"};
            blockRgb = "60,80,140";
            flashRgb = "255,190,40";
            leader = "rgba(40,44,58,0.25)";
        } else {
            backdrop = "#0b0f1a";
            dim = "rgba(5,7,13,0.7)";
            floorLine = null;
            laneEven = "rgba(18,24,41,0.42)";
            laneOdd = "rgba(15,20,34,0.34)";
            laneFlash = "rgba(38,48,77,0.8)";
            hitLine = "#e8e8f0";
            notes = new String[] {"#ff3b6b", "#3bb3ff", "#ff3b6b", "#3bb3ff"};
            laneKey = "#c0c6da";
            laneLabel = "#9aa3c0";
            gridMajor = "rgba(140,180,255,0.45)";
            gridMinor = "rgba(120,150,210,0.22)";
            origin = "rgba(255,224,102,0.9)";
            originStand = "rgba(255,224,102,0.35)";
            regionFill = "rgba(110,160,255,0.22)";
            regionFillLabelOnly = "rgba(160,170,200,0.18)";
            regionText = "rgba(235,240,255,0.95)";
            regionTextLabelOnly = "rgba(190,195,215,0.75)";
            neuron = "#8fd0ff";
            neuronHot = "#ffffff";
            excitIdle = "rgba(150,220,255,0.35)";
            inhibIdle = "rgba(255,90,110,0.18)";
            excitFlashRgb = "120,255,200";
            inhibFlashRgb = "255,90,110";
            caption = "rgba(255,184,107,0.95)";
            hudText = "#ffffff";
            bodyClass = "theme-ar";
            tileFill = "rgba(140,180,255,0.10)";
            tileEdge = "rgba(170,200,255,0.6)";
            flyBody = "rgba(210,220,240,0.85)";
            flyLine = "rgba(210,220,240,0.7)";
            saberCore = new String[] {"#ff5c85", "#5cc4ff"};
            saberGlow = new String[] {"rgba(255,59,107,0.3)", "rgba(59,179,255,0.3)"};
            blockRgb = "170,200,255";
            flashRgb = "255,240,150";
            leader = "rgba(210,220,240,0.3)";
        }
    }

    static final Theme LIGHT = new Theme(true);
    static final Theme AR = new Theme(false);
}
