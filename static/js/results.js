// Renders the two results charts (sample price paths + terminal-price
// histogram) from the JSON payload embedded by the server, and provides
// client-side PNG export of each chart canvas (no server round-trip needed).
(function () {
  var raw = document.getElementById("chart-data");
  if (!raw) return;
  var data = JSON.parse(raw.textContent);

  var PRIMARY = "#4f8cff";
  var ACCENT = "#34d3a5";
  var MUTED = "#93a1bd";
  var GRID = "#26314a";

  // ---- Sample paths (line chart) ----
  var pathsCtx = document.getElementById("pathsChart").getContext("2d");
  var pathDatasets = data.sample_paths.map(function (path, i) {
    return {
      data: path,
      borderColor: "rgba(79, 140, 255, " + (0.15 + 0.1 * Math.random()) + ")",
      borderWidth: 1,
      pointRadius: 0,
      fill: false,
      tension: 0.05,
    };
  });

  new Chart(pathsCtx, {
    type: "line",
    data: { labels: data.time_axis, datasets: pathDatasets },
    options: {
      responsive: true,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { title: { display: true, text: "Time (years)", color: MUTED }, ticks: { color: MUTED, maxTicksLimit: 10 }, grid: { color: GRID } },
        y: { title: { display: true, text: "Price", color: MUTED }, ticks: { color: MUTED }, grid: { color: GRID } },
      },
    },
  });

  // ---- Terminal price histogram (bar chart) ----
  var histCtx = document.getElementById("histChart").getContext("2d");
  var edges = data.histogram.bin_edges;
  var labels = [];
  for (var i = 0; i < edges.length - 1; i++) {
    labels.push(((edges[i] + edges[i + 1]) / 2).toFixed(2));
  }

  new Chart(histCtx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        data: data.histogram.counts,
        backgroundColor: ACCENT,
        borderRadius: 2,
        barPercentage: 1.0,
        categoryPercentage: 1.0,
      }],
    },
    options: {
      responsive: true,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { title: { display: true, text: "Terminal price", color: MUTED }, ticks: { color: MUTED, maxTicksLimit: 10 }, grid: { display: false } },
        y: { title: { display: true, text: "Frequency", color: MUTED }, ticks: { color: MUTED }, grid: { color: GRID } },
      },
    },
  });

  // ---- PNG export ----
  window.downloadChart = function (canvasId, filename) {
    var canvas = document.getElementById(canvasId);
    // Chart.js canvases have a transparent background by default; composite
    // onto a solid background so exported PNGs look right outside the app.
    var tmp = document.createElement("canvas");
    tmp.width = canvas.width;
    tmp.height = canvas.height;
    var ctx = tmp.getContext("2d");
    ctx.fillStyle = "#121a2b";
    ctx.fillRect(0, 0, tmp.width, tmp.height);
    ctx.drawImage(canvas, 0, 0);

    var link = document.createElement("a");
    link.download = filename;
    link.href = tmp.toDataURL("image/png");
    link.click();
  };
})();
