function updateHistoricalPlot(convertSelectedBroadcaster, startedAt) {
    const loadingOverlay = document.getElementById("loadingOverlayHistorical");
    loadingOverlay.style.display = "block";
    
    var xmlHttp = new XMLHttpRequest();

    if (startedAt) {
        xmlHttp.open( "GET", `/api/historical_data?channel=${convertSelectedBroadcaster}&started_at=${startedAt}`, true );
    }
    else {
        xmlHttp.open( "GET", `/api/historical_data?channel=${convertSelectedBroadcaster}`, true );
    };
    xmlHttp.onload = function () {
        loadingOverlay.style.display = "none";
        if (xmlHttp.status === 200) {
            var responseHtml = xmlHttp.responseText;
            var responseJson = JSON.parse(responseHtml);

            let scheduleArray = responseJson.schedule; // get the values of started_at
            console.log("scheduleArray:", scheduleArray);
            const scheduleHeader = document.getElementById("scheduleHeader");

            const startedAtElements = document.getElementsByClassName("startedAt");
            while (startedAtElements.length > 0) { // delete schedule when select a default channel
                scheduleHeader.removeChild(startedAtElements[0]);
            };
            console.log(scheduleArray);
            for (var i = 0; i < scheduleArray.length; i ++) { // create startedDate options

                let startedAt = document.createElement("p");
                startedAt.setAttribute("class", "startedAt");
                startedAt.textContent = scheduleArray[i];

                // parse the textContent of the selectedDate into the bson format which is required by flask.
                startedAt.addEventListener("click", function () { // set event listener to startedAt
                    selectedDate = startedAt.textContent;
                    console.log("selectedDate:", selectedDate);

                    const parts = selectedDate.split(' ');
                    const datePart = parts[0];
                    const timePart = parts[1];
                    const formattedDate = `${datePart}T${timePart}+08:00`;
                    console.log("formattedDate:", formattedDate);
                    
                    // use convertSelectedBroadcaster to select by snake case name
                    updateHistoricalPlot(convertSelectedBroadcaster, formattedDate);
                });

                scheduleHeader.appendChild(startedAt);
            }

            let stats = responseJson.stats; // get the stats data
            console.log(stats.length);

            const channel = stats.map(stats => stats.channel)[0];
            console.log("selectedBroadcaster: ", channel);
            const selectedChannelElement = document.getElementById("selectedBroadcaster");
            selectedChannelElement.textContent = `${selectedBroadcaster}`;
            // selectedChannelElement.appendChild(scheduleHeader);

            const timestamp = stats.map(stats => new Date(stats.timestamp*1000));
            const avgViewerCount = stats.map(stats => stats.avgViewerCount);
            console.log(avgViewerCount)

            const messageCount = stats.map(stats => stats.messageCount);
            // console.log(messageCount)

            const chatterCount = stats.map(stats => stats.chatterCount);
            // console.log(chatterCount)

            const cheer = stats.map(stats => stats.cheers.length);
            // console.log(cheer)

            const sentiment = stats.map(stats => stats.sentiment);
            // console.log(sentiment);

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
                y: sentiment,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'red'},
                name: 'Chatroom Sentiment',
                visible: 'legendonly'
            };

            const trace4 = {
                x: timestamp,
                y: cheer,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'gray'},
                name: 'Cheers',
                visible: 'legendonly'
            };

            const trace5 = {
                x: timestamp,
                y: avgViewerCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'black'},
                name: 'Cheers',
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
                    title: 'Chatroom Engagement'
                },
            };

            const layout2 = {
                
                // title: `${selectedBroadcaster}'s Live Stream Records`,
                font: {
                    family: 'Verdana',
                    size: 15,
                },
                xaxis: {
                    title: 'Time'
                },
                yaxis: {
                    title: 'Viewer Count'
                },
            };

            Plotly.newPlot(
                    'historicalPlot', 
                    [
                        trace1, 
                        trace2, 
                        trace3, 
                        trace4
                    ], 
                    layout1
                ); 

            Plotly.newPlot(
                'historicalPlotViewerCount', 
                [
                    trace5
                ], 
                layout2
            ); 

        }
    }
    xmlHttp.send();
};

const defaultBroadcasters = document.getElementsByClassName("defaultBroadcasters")
for (var i = 0; i < defaultBroadcasters.length; i++) {
    let defaultBroadcaster = defaultBroadcasters[i];
    defaultBroadcaster.addEventListener("click", function () {

        selectedBroadcaster = defaultBroadcaster.textContent;
        convertSelectedBroadcaster = selectedBroadcaster.toLowerCase().replace(/\s+/g, '_');
        updateHistoricalPlot(convertSelectedBroadcaster, null); // set startedAt=null when first loading to the page

    });
};