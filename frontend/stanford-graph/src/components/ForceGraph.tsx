'use client';

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

/* define types */
export interface Node {
  id: string;
  label: string;
}

export interface Edge {
  source: string;
  target: string;
}

/* overall graph structure */
export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

/* render force-directed graph */
export const ForceGraph = ({ data }: { data: GraphData }) => {
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!ref.current || !data?.nodes || !data?.edges) return;

    const width = window.innerWidth;
    const height = window.innerHeight;

    const svg = d3.select(ref.current);
    svg.selectAll('g').remove();  // Remove only the g element, not everything.

    svg.attr('viewBox', `0 0 ${width} ${height}`);
    
    const g = svg.append('g');

    /* D3 force simulation setup */
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.edges).id((d: any) => d.id).distance(60).strength(1))
      .force('charge', d3.forceManyBody().strength(-300)) // try -80 or -100
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(20).strength(0.7))
      .force('radial', d3.forceRadial(200, width / 2, height / 2).strength(0.3));
    
    for (let i = 0; i < 300; ++i) simulation.tick();
    simulation.alpha(0.3).restart();
      

    /* draw edges */
    const edge = g.selectAll('line')
      .data(data.edges)
      .enter()
      .append('line')
      .attr('stroke', '#aaa')
      .attr('stroke-width', 1.3);

    /* draw nodes */
    const node = g.selectAll('circle')
      .data(data.nodes)
      .enter()
      .append('circle')
      .attr('r', 15)
      .attr('fill', d => {
        const isConnected = data.edges.some(edge => {
          const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
          const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
          return sourceId === d.id || targetId === d.id;
        });
        return isConnected ? '#4f46e5' : '#9DFF00';
      })
            
      .call(
        d3.drag<SVGCircleElement, Node>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    /* draw text labels */
    const text = g.selectAll('text')
      .data(data.nodes)
      .enter()
      .append('text')
      .text(d => d.label)
      .attr('font-size', 12)
      .attr('fill', '#ffffff')
      .attr('x', 10)
      .attr('y', 4);
    
    const padding = 20;
    const minX = padding;
    const maxX = width - padding;
    const minY = padding;
    const maxY = height - padding;

    /* update positions on each tick */
    simulation.on('tick', () => {
      data.nodes.forEach((d) => {
        d.x = Math.max(minX, Math.min(maxX, d.x!));
        d.y = Math.max(minY, Math.min(maxY, d.y!));
      });
      edge
        .attr('x1', (d: any) => d.source.x!)
        .attr('y1', (d: any) => d.source.y!)
        .attr('x2', (d: any) => d.target.x!)
        .attr('y2', (d: any) => d.target.y!);

      node
        .attr('cx', d => d.x!)
        .attr('cy', d => d.y!);

      text
        .attr('x', d => d.x! + 10)
        .attr('y', d => d.y! + 4);
    });

  }, [data]);

  return (
    <>
      <svg
        ref={ref}
        className="fixed top-0 left-0 w-screen h-screen"
        style={{ backgroundColor: "black" }}
      >
        {/* BACKGROUND TITLE (centered, pulsing) */}
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="background-title"
        >
          🌲
          DA STANFORD FOREST
          🌲
        </text>
      </svg>
  
      <style jsx global>{`
        .background-title {
          font-size: 90px;
          fill: white;
          opacity: 0.03;
          font-weight: 900;
          letter-spacing: 2px;
          text-transform: uppercase;
          pointer-events: none;
          animation: pulseZoom 10s ease-in-out infinite;
          transform-origin: center;
        }
  
        @keyframes pulseZoom {
          0% {
            transform: scale(1);
            opacity: 0.10;
          }
          50% {
            transform: scale(1.08);
            opacity: 0.15;
          }
          100% {
            transform: scale(1);
            opacity: 0.10;
          }
        }
      `}</style>
    </>
  );
};