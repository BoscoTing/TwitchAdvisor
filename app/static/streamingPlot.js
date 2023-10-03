function trackStreamingChat(selectedChannel) {
    const loadingOverlay = document.getElementById("loadingOverlayStreaming");
    loadingOverlay.style.display = "block";
    console.log("streaming_logs:", loadingOverlay.style.display);

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", `/api/streaming_logs?channel=${selectedChannel}`, false ); 
    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            console.log(xmlHttp.status);
        }
    }
    xmlHttp.send();
    console.log(`listen to ${selectedChannel}'s chatroom`);
}

function updateStreamingPlot(selectedChannel) {

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", `/api/streaming_stats?channel=${selectedChannel}`, true ); 
    // xmlHttp.setRequestHeader('Connection', 'keep-alive');


    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            var responseHtml = xmlHttp.responseText;
            var responseJson = JSON.parse(responseHtml);
            let stats = responseJson.stats; // get the stats data

            const avgViewerCount = stats.map(stats => stats.avgViewerCount)[-1];
            console.log("avgViewerCount: ", avgViewerCount);
            const avgViewerCountElement = document.getElementById("avgViewerCount");
            avgViewerCountElement.textContent = avgViewerCount;


            // const startedAt = stats.startedAt;
            const timestamp = stats.map(stats => new Date(stats.timestamp*1000));
            const messageCount = stats.map(stats => stats.messageCount);
            const chatterCount = stats.map(stats => stats.chatterCount);
            const cheer = stats.map(stats => stats.cheers.length);
            console.log("updating: ", messageCount.length);
            if (messageCount.length == 0) {
                const loadingOverlay = document.getElementById("loadingOverlayStreaming");
                loadingOverlay.style.display = "block";
            }
            else {
                const loadingOverlay = document.getElementById("loadingOverlayStreaming");
                loadingOverlay.style.display = "none";
            }

            const trace1 = {
                x: timestamp,
                y: avgViewerCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'red'},
                name: 'Average Viewers'
            };

            const trace2 = {
                x: timestamp,
                y: messageCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'blue'},
                name: 'messages'
            };

            const trace3 = {
                x: timestamp,
                y: chatterCount,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'green'},
                name: 'chatters'
            };

            const trace4 = {
                x: timestamp,
                y: cheer,
                type: 'scatter',
                mode: 'lines',
                marker: {color: 'gray'},
                name: 'cheer'
            };
            
            // Layout for the chart
            const layout = {
                title: `${selectedChannel}'s chatroom`,
                xaxis: {
                    title: 'Timestamp'
                },
                yaxis: {
                    title: 'Average Viewer Count'
                }
            };
            Plotly.react(
                    'streamingPlot', 
                    [
                        // trace1, 
                        trace2, 
                        // trace3, 
                        trace4
                    ], 
                    layout
                );
        }
    }
    xmlHttp.send();
};


const liveChannels = document.getElementsByClassName("liveChannels");

function updateAfterSelectingChannel() {
    if (selectedChannel) {
        updateStreamingPlot(selectedChannel);
    }
;}

function startUpdateInterval() {
    updateInterval = setInterval(updateAfterSelectingChannel, 5000);
};

for (var i = 0; i < liveChannels.length; i++) {
    let liveChannel = liveChannels[i]
    liveChannel.addEventListener("click", function () {
        selectedChannel = liveChannel.textContent;
        console.log("latest selected channel: ", selectedChannel);

        clearInterval(updateInterval); // stop updating previous selected channel
        console.log("clear the update interval for previous selected channel.")

        trackStreamingChat(selectedChannel);

        updateStreamingPlot(selectedChannel);

        startUpdateInterval();

    });
};