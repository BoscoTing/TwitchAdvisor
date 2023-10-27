function updateHistoricalPlot(convertSelectedBroadcaster, startedAt) {
    const loadingOverlay = document.getElementById("loadingOverlayHistorical");
    loadingOverlay.style.display = "block";

    let xmlHttp = new XMLHttpRequest();

    if (startedAt) {
        xmlHttp.open( "GET", `/api/historical_data?channel=${convertSelectedBroadcaster}&started_at=${startedAt}`, true );
    }
    else {
        xmlHttp.open( "GET", `/api/historical_data?channel=${convertSelectedBroadcaster}`, true );
    };
    xmlHttp.onload = function () {
        loadingOverlay.style.display = "none";
        if (xmlHttp.status === 200) {
            let responseHtml = xmlHttp.responseText;
            let responseJson = JSON.parse(responseHtml);

            let scheduleArray = responseJson.schedule; // get the values of started_at
            const scheduleHeader = document.getElementById("scheduleHeader");

            const startedAtElements = document.getElementsByClassName("startedAt");
            while (startedAtElements.length > 0) { // delete schedule when select a default channel
                scheduleHeader.removeChild(startedAtElements[0]);
            };

            // when using textContent
            for (let i = 0; i < scheduleArray.length; i ++) { // create startedDate options

                let startedAt = document.createElement("option");
                startedAt.setAttribute("class", "startedAt");
                startedAt.textContent = scheduleArray[i];

                scheduleHeader.appendChild(startedAt);
            }

            let stats = responseJson.stats; // get the stats data

            const timestamp = stats.map(stats => new Date(stats.timestamp*1000));
            const avgViewerCount = stats.map(stats => stats.averageViewerCount);
            const messageCount = stats.map(stats => stats.messageCount);
            const chatterCount = stats.map(stats => stats.chatterCount);
            const cheer = stats.map(stats => stats.cheers.length);

            const trace1 = {
                x: timestamp,
                y: messageCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'blue'},
                name: 'Messages'
            };

            const trace2 = {
                x: timestamp,
                y: chatterCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'green'},
                name: 'Chatters'
            };

            const trace3 = {
                x: timestamp,
                y: cheer,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'gray'},
                name: 'Cheers',
                visible: 'legendonly'
            };

            const trace4 = {
                x: timestamp,
                y: avgViewerCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'black'},
                name: 'Viewer Count',
                visible: 'legendonly'

            };

            // Layout for the chart
            const layout1 = {
                title: `${selectedBroadcaster}'s Live Stream Records`,
                font: {
                    family: 'Verdana',
                    size: 15,
                },
                xaxis: {
                    title: 'Time'
                },
                yaxis: {
                    title: "Chatroom activity"
                },
            };
            Plotly.newPlot(
                    'historicalPlot',
                    [
                        trace1,
                        trace2,
                        trace3,
                        trace4,
                    ],
                    layout1
                );
        }
    }
    xmlHttp.send();
};

// when using dropdown selector on Broadcaster
function handleSelectionChange() {

    const selectElement = document.getElementById("broadcasterSelect");
    selectedValue = selectElement.value;
    selectedBroadcaster = selectedValue;
    convertSelectedBroadcaster = selectedBroadcaster.toLowerCase().replace(/\s+/g, '_');
    updateHistoricalPlot(convertSelectedBroadcaster, null); // set startedAt=null when first loading to the page
  }

const selectElement = document.getElementById("broadcasterSelect");
selectElement.addEventListener("change", handleSelectionChange);

// when using dropdown selector on schedule
scheduleHeader.addEventListener("change", function () { // set event listener to startedAt

    selectedDate = scheduleHeader.value;

    const parts = selectedDate.split(' ');
    const datePart = parts[0];
    const timePart = parts[1];
    const formattedDate = `${datePart}T${timePart}+08:00`;
    // use convertSelectedBroadcaster to select by snake case name
    updateHistoricalPlot(convertSelectedBroadcaster, formattedDate);
});

defaultBroadcasters = document.getElementsByClassName("defaultBroadcasters");
let selectedValue = defaultBroadcasters[0].value;
let selectedBroadcaster = selectedValue;
let convertSelectedBroadcaster = selectedBroadcaster.toLowerCase().replace(/\s+/g, '_');
updateHistoricalPlot(convertSelectedBroadcaster, null);