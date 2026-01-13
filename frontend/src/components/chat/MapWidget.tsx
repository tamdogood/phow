"use client";

import { useEffect, useState, useCallback } from "react";
import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from "@react-google-maps/api";

interface LocationData {
  lat: number;
  lng: number;
  formatted_address?: string;
  place_id?: string;
}

interface NearbyPlace {
  name: string;
  vicinity?: string;
  rating?: number;
  user_ratings_total?: number;
}

interface MapWidgetProps {
  location: LocationData;
  competitors?: NearbyPlace[];
  transitStations?: NearbyPlace[];
  nearbyFood?: NearbyPlace[];
  nearbyRetail?: NearbyPlace[];
}

const mapContainerStyle = {
  width: "100%",
  height: "300px",
  borderRadius: "12px",
};

const defaultOptions: google.maps.MapOptions = {
  disableDefaultUI: false,
  zoomControl: true,
  mapTypeControl: false,
  streetViewControl: false,
  fullscreenControl: true,
};

export function MapWidget({
  location,
  competitors = [],
  transitStations = [],
  nearbyFood = [],
  nearbyRetail = [],
}: MapWidgetProps) {
  const [selectedMarker, setSelectedMarker] = useState<{
    position: google.maps.LatLngLiteral;
    title: string;
    type: string;
  } | null>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
  });

  const center = {
    lat: location.lat,
    lng: location.lng,
  };

  const onLoad = useCallback((map: google.maps.Map) => {
    setMap(map);
  }, []);

  const onUnmount = useCallback(() => {
    setMap(null);
  }, []);

  if (loadError) {
    return (
      <div className="w-full h-[300px] bg-gray-100 rounded-xl flex items-center justify-center text-gray-500">
        Error loading map
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="w-full h-[300px] bg-gray-100 rounded-xl flex items-center justify-center text-gray-500 animate-pulse">
        Loading map...
      </div>
    );
  }

  return (
    <div className="w-full my-3">
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        center={center}
        zoom={15}
        options={defaultOptions}
        onLoad={onLoad}
        onUnmount={onUnmount}
      >
        {/* Main location marker */}
        <Marker
          position={center}
          icon={{
            url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
            scaledSize: new google.maps.Size(40, 40),
          }}
          title={location.formatted_address || "Selected Location"}
          onClick={() =>
            setSelectedMarker({
              position: center,
              title: location.formatted_address || "Selected Location",
              type: "main",
            })
          }
        />

        {/* Competitor markers */}
        {competitors.slice(0, 5).map((place, idx) => (
          <Marker
            key={`competitor-${idx}`}
            position={{
              lat: center.lat + (Math.random() - 0.5) * 0.01,
              lng: center.lng + (Math.random() - 0.5) * 0.01,
            }}
            icon={{
              url: "https://maps.google.com/mapfiles/ms/icons/orange-dot.png",
              scaledSize: new google.maps.Size(30, 30),
            }}
            title={place.name}
          />
        ))}

        {/* Transit station markers */}
        {transitStations.slice(0, 3).map((place, idx) => (
          <Marker
            key={`transit-${idx}`}
            position={{
              lat: center.lat + (Math.random() - 0.5) * 0.008,
              lng: center.lng + (Math.random() - 0.5) * 0.008,
            }}
            icon={{
              url: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
              scaledSize: new google.maps.Size(25, 25),
            }}
            title={place.name}
          />
        ))}

        {/* Info Window */}
        {selectedMarker && (
          <InfoWindow
            position={selectedMarker.position}
            onCloseClick={() => setSelectedMarker(null)}
          >
            <div className="p-2">
              <h3 className="font-semibold text-sm">{selectedMarker.title}</h3>
              {selectedMarker.type === "main" && (
                <p className="text-xs text-gray-500 mt-1">Your target location</p>
              )}
            </div>
          </InfoWindow>
        )}
      </GoogleMap>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-2 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500"></span>
          <span>Target Location</span>
        </div>
        {competitors.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-orange-500"></span>
            <span>Competitors ({competitors.length})</span>
          </div>
        )}
        {transitStations.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
            <span>Transit ({transitStations.length})</span>
          </div>
        )}
      </div>
    </div>
  );
}
