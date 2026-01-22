"use client";

import { useMemo } from "react";
import { GoogleMap, useJsApiLoader, Marker } from "@react-google-maps/api";

const mapContainerStyle = {
  width: "100%",
  height: "100%",
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
    { elementType: "labels.text.fill", stylers: [{ color: "#6b7280" }] },
    { featureType: "road", elementType: "geometry", stylers: [{ color: "#2d2d44" }] },
    { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#6b7280" }] },
    { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#3d3d5c" }] },
    { featureType: "water", elementType: "geometry", stylers: [{ color: "#0c3654" }] },
    { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] },
    { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#1a2e1a" }] },
    { featureType: "transit", stylers: [{ visibility: "off" }] },
  ],
};

// Demo location: San Francisco downtown (shifted right to be visible on the right side)
const SF_CENTER = { lat: 37.7879, lng: -122.3974 };

// Demo competitor locations around SF
const DEMO_COMPETITORS = [
  { lat: 37.7895, lng: -122.3915 },
  { lat: 37.7855, lng: -122.3995 },
  { lat: 37.7910, lng: -122.4010 },
  { lat: 37.7840, lng: -122.3940 },
  { lat: 37.7870, lng: -122.4030 },
  { lat: 37.7920, lng: -122.3950 },
  { lat: 37.7835, lng: -122.4020 },
];

// Demo transit stations
const DEMO_TRANSIT = [
  { lat: 37.7869, lng: -122.3990 },
  { lat: 37.7901, lng: -122.3910 },
];

export function HeroMapDemo() {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
  });

  const center = useMemo(() => SF_CENTER, []);

  if (loadError || !isLoaded) {
    return <div className="w-full h-full bg-slate-900" />;
  }

  return (
    <GoogleMap
      mapContainerStyle={mapContainerStyle}
      center={center}
      zoom={15}
      options={mapOptions}
    >
      {/* Main target location */}
      <Marker
        position={{ lat: 37.7879, lng: -122.3974 }}
        icon={{
          url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
          scaledSize: new google.maps.Size(44, 44),
        }}
      />

      {/* Competitor markers */}
      {DEMO_COMPETITORS.map((pos, idx) => (
        <Marker
          key={`comp-${idx}`}
          position={pos}
          icon={{
            url: "https://maps.google.com/mapfiles/ms/icons/orange-dot.png",
            scaledSize: new google.maps.Size(32, 32),
          }}
        />
      ))}

      {/* Transit markers */}
      {DEMO_TRANSIT.map((pos, idx) => (
        <Marker
          key={`transit-${idx}`}
          position={pos}
          icon={{
            url: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
            scaledSize: new google.maps.Size(28, 28),
          }}
        />
      ))}
    </GoogleMap>
  );
}
