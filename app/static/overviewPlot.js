function updateOverviewPlot(selectedWeek) {
    const loadingOverlay = document.getElementById("loadingOverlayOverview");
    loadingOverlay.style.display = "block";
    
    var xmlHttp = new XMLHttpRequest();
    if (selectedWeek) {
        xmlHttp.open( "GET", `/api/overview_data?week=${selectedWeek}`, true );
        console.log("GET", `/api/overview_data?week=${selectedWeek}`);
    }
    else {
        xmlHttp.open( "GET", `/api/overview_data`, true ); // use default week in flask
        console.log(`/api/overview_data`);
    };
    xmlHttp.onload = function () {
        loadingOverlay.style.display = "none";
        if (xmlHttp.status === 200) {
            var responseHtml = xmlHttp.responseText;
            var data = JSON.parse(responseHtml);
            console.log("data: " ,data);

            // Extract unique channels
            const channels = [...new Set(data.map(entry => entry.channel))];
            console.log("channels: ", channels);

            // Create an array of all weekdays
            const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

            // Create data traces for each channel
            const traces = channels.map(channel => {
                const channelData = data.filter(entry => entry.channel === channel);
                const xValues = weekdays;
                const yValues = weekdays.map(weekday => {
                    const entry = channelData.find(dataEntry => dataEntry.weekDayName === weekday);
                    if (entry) {
                        console.log("entry: ", entry)
                    };
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
            Plotly.react('overviewPlot', traces, layout);
        }
    };
    xmlHttp.send();
}


updateOverviewPlot();

const weekOptions = document.getElementsByClassName("weekOptions")
for (var i = 0; i < weekOptions.length; i++) {
    let weekOption = weekOptions[i];
    weekOption.addEventListener("click", function () {

        const weekText = weekOption.textContent;
        const match = weekText.match(/\d+/);
        if (match) {
            // Extracted week number
            const selectedWeek = match[0];
            console.log('selectedWeek:', selectedWeek);
            updateOverviewPlot(selectedWeek, null);
        } else {
            console.log('Week number not found in text:', weekText);
        };
    });
};