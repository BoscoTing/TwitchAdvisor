function updateStreamingPlot(selectedChannel) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", `/api/streaming_logs?channel=${selectedChannel}`, true ); 
    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            console.log(xmlHttp.status);
        }
    }
    xmlHttp.send();

    xmlHttp.open( "GET", `/api/streaming_stats?channel=${selectedChannel}`, true ); 
    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            var responseHtml = xmlHttp.responseText;
            var responseJson = JSON.parse(responseHtml);
            console.log(responseJson)
            let stats = responseJson.stats; // get the stats data
            const channel = stats.channel;
            const startedAt = stats.startedAt;
            const timestamp = stats.map(stats => new Date(stats.timestamp*1000));
            const avgViewerCount = stats.map(stats => stats.avgViewerCount);
            const messageCount = stats.map(stats => stats.messageCount);
            const chatterCount = stats.map(stats => stats.chatterCount);
            const cheer = stats.map(stats => stats.cheers.length);
            console.log(cheer)

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
                title: 'Average Viewer Count Over Time',
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

let selectedChannel = null;

for (var i = 0; i < liveChannels.length; i++) {
    let liveChannel = liveChannels[i]
    liveChannel.addEventListener("click", function () {
        selectedChannel = liveChannel.textContent;
        console.log(selectedChannel);
        updateStreamingPlot(selectedChannel);
    });
};

function updateAfterSelectingChannel() {
    if (selectedChannel) {
        updateStreamingPlot(selectedChannel);
    }
;}

// updateStreamingPlot(liveChannels);
var updateInterval = setInterval(updateAfterSelectingChannel, 5000); // update in every 5 seconds.