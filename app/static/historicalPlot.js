function updateHistoricalPlot(selectBroadcaster, startedAt) {
    const loadingOverlay = document.getElementById("loadingOverlayHistorical");
    loadingOverlay.style.display = "block";
    
    var xmlHttp = new XMLHttpRequest();
    // selectBroadcaster = document.getElementsByClassName("defaultBroadcasters").value;
    // var host = window.location.host; 
    if (startedAt) {
        xmlHttp.open( "GET", `/api/historical_data?channel=${selectBroadcaster}&started_at=${startedAt}`, true );
    }
    else {
        xmlHttp.open( "GET", `/api/historical_data?channel=${selectBroadcaster}`, true );
    };
    xmlHttp.onload = function () {
        loadingOverlay.style.display = "none";
        if (xmlHttp.status === 200) {
            var responseHtml = xmlHttp.responseText;
            var responseJson = JSON.parse(responseHtml);

            let scheduleArray = responseJson.schedule; // get the values of started_at
            console.log(scheduleArray);
            const scheduleHeader = document.getElementById("scheduleHeader");

            const startedAtElements = document.getElementsByClassName("startedAt");
            while (startedAtElements.length > 0) { // delete schedule when select a default channel
                scheduleHeader.removeChild(startedAtElements[0]);
            };
            console.log(scheduleArray);
            for (var i = 0; i < scheduleArray.length; i ++) { // create startedDate options
                console.log(scheduleArray[i]);
                let startedAt = document.createElement("p");
                startedAt.setAttribute("class", "startedAt");
                startedAt.textContent = scheduleArray[i];

                startedAt.addEventListener("click", function () { // set event listener to startedAt
                    selectedDate = startedAt.textContent;
                    console.log(selectedDate);
                    updateHistoricalPlot(selectBroadcaster, selectedDate);
                });

                scheduleHeader.appendChild(startedAt);
            }

            let stats = responseJson.stats; // get the stats data
            console.log(stats.length);

            const channel = stats.map(stats => stats.channel)[0];
            console.log("selectedBroadcaster: ", channel);
            const selectedChannelElement = document.getElementById("selectedBroadcaster");
            selectedChannelElement.textContent = `${channel}'s channel`;
            selectedChannelElement.appendChild(scheduleHeader);
            // const cheers = stats.cheers;
            // const startedAt = stats.startedAt;
            const timestamp = stats.map(stats => new Date(stats.timestamp*1000));
            const avgViewerCount = stats.map(stats => stats.avgViewerCount);
            const messageCount = stats.map(stats => stats.messageCount);
            const chatterCount = stats.map(stats => stats.chatterCount);
            const cheer = stats.map(stats => stats.cheers.length);

            const sentiment = stats.map(stats => stats.sentiment);
            console.log(sentiment);

            const trace1 = {
                x: timestamp,
                y: sentiment,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'red'},
                name: 'Chatroom Sentiment'
            };

            const trace2 = {
                x: timestamp,
                y: messageCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'blue'},
                name: 'Messages'
            };

            const trace3 = {
                x: timestamp,
                y: chatterCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'green'},
                name: 'Chatters'
            };

            const trace4 = {
                x: timestamp,
                y: cheer,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'gray'},
                name: 'Cheers'
            };
            
            // Layout for the chart
            const layout = {
                title: 'Average Viewer Count Over Time',
                xaxis: {
                    title: 'Timestamp'
                },
                yaxis: {
                    title: 'Average Viewer Count'
                }
            };

            Plotly.newPlot(
                    'historicalPlot', 
                    [
                        trace1, 
                        trace2, 
                        trace3, 
                        trace4
                    ], 
                    layout
                );    
        }
    }
    xmlHttp.send();
};

const defaultBroadcasters = document.getElementsByClassName("defaultBroadcasters")
for (var i = 0; i < defaultBroadcasters.length; i++) {
    let defaultBroadcaster = defaultBroadcasters[i];
    defaultBroadcaster.addEventListener("click", function () {

        selectBroadcaster = defaultBroadcaster.textContent;
        updateHistoricalPlot(selectBroadcaster, null); // set startedAt=null when first loading to the page

    });
};