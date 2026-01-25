"use client";

import { useState, useCallback, useMemo } from "react";
import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from "@react-google-maps/api";
import { MapPin, Store, Train } from "lucide-react";
import { LocationInfoCards } from "../widgets/LocationInfoCards";

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
  price_level?: number;
}

interface MapWidgetProps {
  location: LocationData;
  competitors?: NearbyPlace[];
  transitStations?: NearbyPlace[];
  analysisSummary?: {
    competitor_count?: number;
    transit_access?: boolean;
    foot_traffic_indicators?: number;
  };
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

// Generate deterministic offset based on index
function getOffset(idx: number, scale: number): { lat: number; lng: number } {
  const angle = (idx * 137.5 * Math.PI) / 180; // Golden angle for even distribution
  const radius = scale * (0.3 + (idx % 3) * 0.2);
  return {
    lat: Math.cos(angle) * radius,
    lng: Math.sin(angle) * radius,
  };
}

export function MapWidget({
  location,
  competitors = [],
  transitStations = [],
  analysisSummary,
}: MapWidgetProps) {
  const [selectedMarker, setSelectedMarker] = useState<{
    position: google.maps.LatLngLiteral;
    title: string;
    type: string;
  } | null>(null);

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
  });

  const center = useMemo(() => ({
    lat: location.lat,
    lng: location.lng,
  }), [location.lat, location.lng]);

  const onLoad = useCallback(() => {}, []);
  const onUnmount = useCallback(() => {}, []);

  if (loadError) {
    return (
      <div className="w-full h-[300px] bg-slate-900 rounded-xl flex items-center justify-center text-slate-400 border border-slate-800">
        Error loading map
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="w-full h-[300px] bg-slate-900 rounded-xl flex items-center justify-center text-slate-400 animate-pulse border border-slate-800">
        Loading map...
      </div>
    );
  }

  return (
    <div className="w-full my-3">
      <div className="widget-card p-4 mb-4">
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
        {competitors.slice(0, 5).map((place, idx) => {
          const offset = getOffset(idx, 0.01);
          return (
            <Marker
              key={`competitor-${idx}`}
              position={{
                lat: center.lat + offset.lat,
                lng: center.lng + offset.lng,
              }}
              icon={{
                url: "https://maps.google.com/mapfiles/ms/icons/orange-dot.png",
                scaledSize: new google.maps.Size(30, 30),
              }}
              title={place.name}
            />
          );
        })}

        {/* Transit station markers */}
        {transitStations.slice(0, 3).map((place, idx) => {
          const offset = getOffset(idx + 10, 0.008);
          return (
            <Marker
              key={`transit-${idx}`}
              position={{
                lat: center.lat + offset.lat,
                lng: center.lng + offset.lng,
              }}
              icon={{
                url: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
                scaledSize: new google.maps.Size(25, 25),
              }}
              title={place.name}
            />
          );
        })}

        {/* Info Window */}
        {selectedMarker && (
          <InfoWindow
            position={selectedMarker.position}
            onCloseClick={() => setSelectedMarker(null)}
          >
            <div className="p-2">
              <h3 className="font-semibold text-sm text-slate-900">{selectedMarker.title}</h3>
              {selectedMarker.type === "main" && (
                <p className="text-xs text-slate-600 mt-1">Your target location</p>
              )}
            </div>
          </InfoWindow>
        )}
      </GoogleMap>

      {/* Enhanced Legend */}
      <div className="flex flex-wrap gap-4 mt-3 text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-red-400" />
          <span>Target Location</span>
        </div>
        {competitors.length > 0 && (
          <div className="flex items-center gap-2">
            <Store className="w-4 h-4 text-orange-400" />
            <span>Competitors ({competitors.length})</span>
          </div>
        )}
        {transitStations.length > 0 && (
          <div className="flex items-center gap-2">
            <Train className="w-4 h-4 text-blue-400" />
            <span>Transit ({transitStations.length})</span>
          </div>
        )}
      </div>
      </div>

      {/* Location Info Cards */}
      <LocationInfoCards
        data={{
          competitors,
          transit_stations: transitStations,
          analysis_summary: analysisSummary,
        }}
      />
    </div>
  );
}
