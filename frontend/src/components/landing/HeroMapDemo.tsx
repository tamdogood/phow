"use client";

import { useMemo } from "react";
import { GoogleMap, useJsApiLoader, Marker } from "@react-google-maps/api";

const mapContainerStyle = {
  width: "100%",
  height: "300px",
  borderRadius: "12px",
};

const mapOptions: google.maps.MapOptions = {
  disableDefaultUI: true,
  zoomControl: false,
  mapTypeControl: false,
  streetViewControl: false,
  fullscreenControl: false,
  gestureHandling: "none",
  styles: [
    { elementType: "geometry", stylers: [{ color: "#1a1a2e" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#1a1a2e" }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#8892b0" }] },
    { featureType: "road", elementType: "geometry", stylers: [{ color: "#2d2d44" }] },
    { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#8a8a8a" }] },
    { featureType: "water", elementType: "geometry", stylers: [{ color: "#0e4166" }] },
    { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] },
    { featureType: "transit", stylers: [{ visibility: "off" }] },
  ],
};

// Demo location: San Francisco downtown
const SF_CENTER = { lat: 37.7879, lng: -122.4074 };

// Demo competitor locations around SF
const DEMO_COMPETITORS = [
  { lat: 37.7895, lng: -122.4015, name: "Competitor 1" },
  { lat: 37.7855, lng: -122.4095, name: "Competitor 2" },
  { lat: 37.7910, lng: -122.4110, name: "Competitor 3" },
  { lat: 37.7840, lng: -122.4040, name: "Competitor 4" },
  { lat: 37.7870, lng: -122.4130, name: "Competitor 5" },
];

// Demo transit stations
const DEMO_TRANSIT = [
  { lat: 37.7869, lng: -122.4090, name: "Montgomery St Station" },
  { lat: 37.7901, lng: -122.4010, name: "Embarcadero Station" },
];

export function HeroMapDemo() {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
  });

  const center = useMemo(() => SF_CENTER, []);

  if (loadError) {
    return (
      <div className="w-full h-[300px] bg-slate-800/80 rounded-xl flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">🗺️</div>
          <p className="text-white/60 text-sm">Interactive map preview</p>
        </div>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="w-full h-[300px] bg-slate-800/50 rounded-xl flex items-center justify-center animate-pulse">
        <span className="text-white/40">Loading map...</span>
      </div>
    );
  }

  return (
    <div className="relative">
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        center={center}
        zoom={15}
        options={mapOptions}
      >
        {/* Main target location */}
        <Marker
          position={center}
          icon={{
            url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
            scaledSize: new google.maps.Size(40, 40),
          }}
        />

        {/* Competitor markers */}
        {DEMO_COMPETITORS.map((comp, idx) => (
          <Marker
            key={`comp-${idx}`}
            position={{ lat: comp.lat, lng: comp.lng }}
            icon={{
              url: "https://maps.google.com/mapfiles/ms/icons/orange-dot.png",
              scaledSize: new google.maps.Size(28, 28),
            }}
          />
        ))}

        {/* Transit markers */}
        {DEMO_TRANSIT.map((station, idx) => (
          <Marker
            key={`transit-${idx}`}
            position={{ lat: station.lat, lng: station.lng }}
            icon={{
              url: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
              scaledSize: new google.maps.Size(24, 24),
            }}
          />
        ))}
      </GoogleMap>

      {/* Legend overlay */}
      <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-sm rounded-lg px-3 py-2 flex items-center gap-4 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
          <span className="text-white/70">Your Location</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
          <span className="text-white/70">Competitors</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
          <span className="text-white/70">Transit</span>
        </div>
      </div>
    </div>
  );
}
