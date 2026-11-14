import Plot from 'react-plotly.js';

export default function EvalChart({ evalData, colorData, onSelect }) {
  return <Plot
    data={[{
      x: evalData.map((_, index) => index + 1), y: evalData, mode: 'lines+markers',
      marker: { size: 7, color: colorData }, line: { color: '#888', width: 2 },
    }]}
    layout={{ width: 550, height: 280, margin: { t: 20, b: 40, l: 60, r: 20 }, xaxis: { title: { text: 'Move index' } }, yaxis: { autorange: true } }}
    config={{ responsive: true }}
    onClick={event => onSelect?.(event.points[0].pointIndex)}
  />;
}
