'use client';

import { useEffect, useState } from 'react';
import { ForceGraph, GraphData } from '@/components/ForceGraph';

export default function Home() {
  const [data, setData] = useState<GraphData | null>(null);

  useEffect(() => {
    fetch('/api/graph')
      .then(res => res.json())
      .then(json => setData(json))
      .catch(err => console.error('Failed to load graph:', err));
  }, []);

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold mb-6">🌲🌳DA STANFORD FOREST</h1>
      {data ? (
        <ForceGraph data={data} />
      ) : (
        <p>Loading course data...</p>
      )}
    </main>
  );
}
