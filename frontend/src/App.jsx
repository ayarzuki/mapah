import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import axios from 'axios';

// Fix Leaflet's default icon path issues with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const redIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

function LocationMarker({ position, setPosition }) {
  const map = useMapEvents({
    click(e) {
      setPosition(e.latlng);
      map.flyTo(e.latlng, map.getZoom());
    },
  });

  return position === null ? null : (
    <Marker position={position}>
      <Popup>Selected Location</Popup>
    </Marker>
  );
}

function App() {
  const [position, setPosition] = useState(null);
  const [category, setCategory] = useState('Coffee Shop');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!position) return alert('Please select a location on the map first.');
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/api/analyze', {
        lat: position.lat,
        lng: position.lng,
        category
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert('Error fetching analysis');
    }
    setLoading(false);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-1/3 flex flex-col h-full bg-white shadow-xl z-10">
        <div className="p-6 border-b">
          <h1 className="text-2xl font-bold text-gray-800">GeoBiz Analyzer</h1>
          <p className="text-gray-500 text-sm mt-1">Evaluate business viability by location.</p>
        </div>
        
        <div className="p-6 flex-1 overflow-y-auto">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              1. Select Business Category
            </label>
            <select 
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-blue-500 focus:border-blue-500"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="Coffee Shop">Coffee Shop</option>
              <option value="Minimarket">Minimarket</option>
              <option value="Laundromat">Laundromat</option>
              <option value="Car Wash">Car Wash</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              2. Click on the Map to drop a pin
            </label>
            <p className="text-sm text-gray-500">
              {position ? `Selected: ${position.lat.toFixed(4)}, ${position.lng.toFixed(4)}` : 'No location selected'}
            </p>
          </div>

          <button 
            onClick={handleAnalyze}
            disabled={loading || !position}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : 'Analyze Viability'}
          </button>

          {result && (
            <div className="mt-8 animate-fade-in-up">
              <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
                <div className="text-center mb-4">
                  <div className="text-sm text-blue-600 font-semibold uppercase tracking-wider">Viability Score</div>
                  <div className="text-5xl font-extrabold text-blue-900 mt-1">{result.score}</div>
                </div>
                
                <h3 className="font-bold text-gray-800 mb-2">SWOT Analysis</h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-green-600 font-bold text-sm uppercase">Strengths</span>
                    <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
                      {result.swot.strengths.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                  <div>
                    <span className="text-red-600 font-bold text-sm uppercase">Weaknesses</span>
                    <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
                      {result.swot.weaknesses.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 h-full relative">
        <MapContainer center={[-6.2415, 106.8123]} zoom={13} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />
          <LocationMarker position={position} setPosition={setPosition} />
          
          {result && result.competitors && result.competitors.map((comp, i) => (
             <Marker key={i} position={[comp.lat, comp.lng]} icon={redIcon}>
               <Popup>Competitor: {comp.name}</Popup>
             </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
