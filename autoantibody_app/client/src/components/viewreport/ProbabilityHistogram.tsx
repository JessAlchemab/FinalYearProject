import React from "react";
import Plot from "react-plotly.js";

interface ProbabilityHistogramProps {
  data: { [key: string]: number };
}

const ProbabilityHistogram: React.FC<ProbabilityHistogramProps> = ({
  data,
}) => {
  // Sort buckets numerically
  const sortedEntries = Object.entries(data).sort((a, b) => {
    const parseFirstNumber = (key: string) => parseFloat(key.split("-")[0]);
    return parseFirstNumber(a[0]) - parseFirstNumber(b[0]);
  });

  const xValues = sortedEntries.map(([key]) => key);
  const yValues = sortedEntries.map(([, value]) => value);

  return (
    <Plot
      data={[
        {
          x: xValues,
          y: yValues,
          type: "bar",
          marker: {
            color: "blue",
            opacity: 0.7,
          },
        },
      ]}
      layout={{
        // title: "Probability Distribution",
        xaxis: {
          title: "Confidence of autoreactivity",
          tickangle: -45,
        },
        yaxis: {
          title: "Percentage of sequences",
        },
        // height: 400,
        // width: "auto",
        autosize: true,
      }}
    />
  );
};

export default ProbabilityHistogram;
