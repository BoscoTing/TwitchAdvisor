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
            // console.log(stats);

            // const startedAt = stats.startedAt;
            const timestamp = stats.map(stats => new Date(stats.timestamp*1000));

            const messageCount = stats.map(stats => stats.messageCount);
            console.log("updating: ", messageCount.length);
            console.log(messageCount);
            const chatterCount = stats.map(stats => stats.chatterCount);
            console.log(chatterCount);
            const cheerCount = stats.map(stats => stats.cheers.length);
            console.log(cheerCount);
            const avgViewerCount = stats.map(stats => stats.averageViewerCount);
            console.log("avgViewerCount: ", avgViewerCount.at(-1));

            // show the avgViewerCount on streaming plot section
            const avgViewerCountElement = document.getElementById("avgViewerCount");
            avgViewerCountElement.textContent = avgViewerCount.at(-1);


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
                y: cheerCount,
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
                    title: 'Chatroom Engagement'
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


// search bar which receives value by pressing enter

const searchBtn = document.getElementById("searchBotton");
const searchBar = document.getElementById("searchBar");
let searchQuery;

searchBar.addEventListener("keydown", (e) => {
    if (e.key == "Enter" && searchBar.value != "") {
        searchQuery = searchBar.value;
        console.log(searchQuery);

        const url = new URL('https://www.twitch.tv/lolworldchampionship');
        const channelName = url.pathname.split('/').pop();
        console.log(channelName); // This will output 'lolworldchampionship'
        
        selectedChannel = channelName; // assign selectedChannel in a broader scope

        console.log("latest selected channel: ", selectedChannel);
        clearInterval(updateInterval); // stop updating previous selected channel
        console.log("clear the update interval for previous selected channel.")

        trackStreamingChat(selectedChannel);
        updateStreamingPlot(selectedChannel);
        startUpdateInterval();
    }

});