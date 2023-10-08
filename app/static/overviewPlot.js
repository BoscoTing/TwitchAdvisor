function updateOverviewPlot() {
    const loadingOverlay = document.getElementById("loadingOverlayOverview");
    loadingOverlay.style.display = "block";
    
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", `/api/overview_data`, true);
    xmlHttp.onload = function () {
        loadingOverlay.style.display = "none";
        if (xmlHttp.status === 200) {
            var responseHtml = xmlHttp.responseText;
            var data = JSON.parse(responseHtml);

            // Extract unique channels
            const channels = [...new Set(data.map(entry => entry.channel))];

            // Create an array of all weekdays
            const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

            // Create data traces for each channel
            const traces = channels.map(channel => {
                const channelData = data.filter(entry => entry.channel === channel);
                const xValues = weekdays;
                const yValues = weekdays.map(weekday => {
                    const entry = channelData.find(dataEntry => dataEntry.dayOfWeek === weekday);
                    return entry ? entry.avgMessageCount : 0;
                });

                return {
                    x: xValues,
                    y: yValues,
                    name: channel,
                    mode: 'markers',
                    type: 'scatter',
                    marker: {"size": 12}
                };
            });

            // Create the layout
            const layout = {
                xaxis: {
                    title: 'Day of the Week'
                },
                yaxis: {
                    title: 'Metric'
                },
                // barmode: 'group'
            };

            // Create the chart
            Plotly.newPlot('overviewPlot', traces, layout);
        }
    };
    xmlHttp.send();
}


updateOverviewPlot();