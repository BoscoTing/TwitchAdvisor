let currentRequestLogs = null;

function trackStreamingChat(selectedChannel) {
    const loadingOverlay = document.getElementById("loadingOverlayStreaming");
    loadingOverlay.style.display = "block"; // Block the screen when ircbot is connecting

    // Check if there's an ongoing request and abort it
    if (currentRequestLogs) {
        currentRequestLogs.abort();
    }

    let xmlHttp = new XMLHttpRequest();
    currentRequestLogs = xmlHttp; // Store the current request

    xmlHttp.open("GET", `/api/streaming_logs?channel=${selectedChannel}`, true);

    // Flask API streaming_logs: start a while loop and won't send a response
    // Set true to make the request asynchronous to do other things:
    // 1. Block the screen
    // 2. startUpdateInterval to updateStreamingPlot

    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            console.log(xmlHttp.status);
        }
        if (xmlHttp.status === 406 && JSON.parse(xmlHttp.responseText).error == "Channel is offline") {
            loadingOverlay.style.display = "none"; // unblock when entering into chatroom failed.
            alert("This channel is offline, or it doesn't exist.");
            selectedChannel = null;
            return null; // don't send the request again with offline channel.
        }
        else if (xmlHttp.status === 406 && JSON.parse(xmlHttp.responseText).error == "Same channel is selected") {
            searchQuery = '';
            loadingOverlay.style.display = "none"; // unblock when entering into chatroom failed.
            return null; // don't send the request again with duplicated channel seleted.
        }
        currentRequestLogs = null; // Reset the current request when it's completed (but here we are going to abort the requests of /api/streaming_logs while switching channels so this line might not works)
    };

    xmlHttp.send();
}

let currentRequestStats = null;
let previousMessageCountLength = null;
function updateStreamingPlot(selectedChannel) {

    let xmlHttp = new XMLHttpRequest();
    currentRequestStats = xmlHttp; // be used in keydown event listener

    xmlHttp.open( "GET", `/api/streaming_stats?channel=${selectedChannel}`, true );

    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            let responseHtml = xmlHttp.responseText;
            let responseJson = JSON.parse(responseHtml);
            let stats = responseJson.stats; // get the stats data
            if (stats == null){ // if channel is offline, streaming_logs API return 406
                clearInterval(updateInterval);
                return null
            };
            // const startedAt = stats.startedAt;
            const timestamp = stats.map(stats => new Date(stats.timestamp*1000));

            const messageCount = stats.map(stats => stats.messageCount);
            const chatterCount = stats.map(stats => stats.chatterCount);
            const cheerCount = stats.map(stats => stats.cheers.length);
            const avgViewerCount = stats.map(stats => stats.averageViewerCount);

            // show the avgViewerCount on streaming plot section
            const avgViewerCountElement = document.getElementById("avgViewerCount");
            avgViewerCountElement.textContent = avgViewerCount.at(-1);

            if (avgViewerCount == null && updateInterval){ // if channel turn off during plotting the streaming chart, clear the update interval.
                clearInterval(updateInterval);
                return null
            };

            const totalCheersElement = document.getElementById("totalCheers");
            if (cheerCount.length >= 1) {
                let totalCheers = cheerCount.reduce(function(a, b){
                    return a + b;
                  });
                totalCheersElement.textContent = totalCheers;
            }

            const loadingOverlay = document.getElementById("loadingOverlayStreaming");
            const waitingMessage = document.getElementById("waitingMessage");

            if (messageCount.length >= 0) {

                loadingOverlay.style.display = "none";

                if (messageCount.length == previousMessageCountLength || messageCount.length <= 1) { // wait for new data to update the chart
                    waitingMessage.style.display = "block";
                }
                else if (messageCount.length > previousMessageCountLength) {
                    waitingMessage.style.display = "none";
                }

                previousMessageCountLength = messageCount.length;

            }
            else {
                const waitingMessage = document.getElementById("waitingMessage");
                waitingMessage.style.display = "none";
            }

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

            // Layout for the chart
            const layout = {
                title: `Live Stream Chatroom: ${processName(selectedChannel)}`,
                font: {
                    family: 'Verdana',
                    size: 15,
                },
                xaxis: {
                    title: 'Time'
                },
                yaxis: {
                    title: "Chatroom activity"
                }
            };
            Plotly.react(
                    'streamingPlot',
                    [
                        trace1,
                        trace2,
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

function DeleteTraces () {
    let graphD = document.getElementById("streamingPlot");
    if (graphD.data) {
        while (graphD.data.length){
            Plotly.deleteTraces(streamingPlot, [0]);
        }
    }
}

function processName(name) {
    // Replace underscores with spaces, capitalize the first letter of each word, and handle "lol" pattern
    name = name.replace(/_/g, ' '); // Replace underscores with spaces
    name = name.replace(/\b\w/g, (match) => match.toUpperCase()); // Capitalize the first letter of each word
    name = name.replace(/_lol\b/gi, 'LOL'); // Handle "lol" pattern
    return name;
  }

let updateInterval = null; // assign updateInterval in initial

for (let i = 0; i < liveChannels.length; i++) {
    let liveChannel = liveChannels[i]
    liveChannel.addEventListener("click", function () {

        selectedChannel = liveChannel.textContent;

        clearInterval(updateInterval); // stop updating previous selected channel

        trackStreamingChat(selectedChannel);

        startUpdateInterval();

    });
};

// search bar which receives value by pressing enter
const searchBtn = document.getElementById("searchButton");
const searchBar = document.getElementById("searchBar");
let searchQuery;

searchBar.addEventListener("keydown", (e) => {
    if (e.key == "Enter" && searchBar.value != "") {

        searchQuery = searchBar.value;
        searchBar.value = '';

        const regex = /^(https?:\/\/)?(www\.)?twitch\.tv\/\w+\/?(?:\?referrer=raid|\/video)?$/; // check if the url is in the format of https://www.twitch.tv, http://www.twitch.tv or www.twitch.tv
        if (regex.test(searchQuery) == false) {
            searchQuery = '';
            alert("Invalid url. Please try again.")
        }

        if (!searchQuery.startsWith("http://") && !searchQuery.startsWith("https://")) { // If url doesn't start with "http" or "https," add "https://"
            searchQuery = "https://" + searchQuery;
          }

        if (currentRequestStats) { // currentRequestStats is assigned in 'updateStreamingPlot' function. If the socket connection is still waiting for messages, we quit that request.
            currentRequestStats.abort();
        }

        try {
            url = new URL(searchQuery);
            channelName = url.pathname.split('/').pop();
        } catch (error) {
            searchQuery = '';
            console.log(error);
        }

        selectedChannel = channelName; // assign selectedChannel in a broader scope

        if (updateInterval) {
            clearInterval(updateInterval); // stop updating previous selected channel
        };

        trackStreamingChat(selectedChannel);

        startUpdateInterval(); //set or reset startUpdateInterval and execute updateStreamingPlot

    }

});

searchBtn.addEventListener("click", (e) => {
    if (searchBar.value != "") {

        searchQuery = searchBar.value;
        searchBar.value = '';

        const regex = /^(https?:\/\/)?(www\.)?twitch\.tv\/\w+\/?(?:\?referrer=raid|\/video)?$/; // check if the url is in the format of https://www.twitch.tv, http://www.twitch.tv or www.twitch.tv
        if (regex.test(searchQuery) == false) {
            searchQuery = '';
            alert("Invalid url. Please try again.")
        }

        if (!searchQuery.startsWith("http://") && !searchQuery.startsWith("https://")) { // If url doesn't start with "http" or "https," add "https://"
            searchQuery = "https://" + searchQuery;
          }

        if (currentRequestStats) { // currentRequestStats is assigned in 'updateStreamingPlot' function. If the socket connection is still waiting for messages, we quit that request.
            currentRequestStats.abort();
        }

        try {
            url = new URL(searchQuery);
            channelName = url.pathname.split('/').pop();
        } catch (error) {
            searchQuery = '';
            console.log(error);
        }

        selectedChannel = channelName; // assign selectedChannel in a broader scope

        if (updateInterval) {
            clearInterval(updateInterval); // stop updating previous selected channel
        };

        trackStreamingChat(selectedChannel);

        startUpdateInterval(); //set or reset startUpdateInterval and execute updateStreamingPlot

    }

});

// window.addEventListener('beforeunload', function () {
//     let xmlHttp = new XMLHttpRequest();
//     xmlHttp.open("GET", `/api/streaming_logs?event=beforeunload`, true);
//     xmlHttp.onload = function () {
//         if (xmlHttp.status === 200) {
//         }
//     };
//     xmlHttp.send();
// });

window.addEventListener('beforeunload', function () {
    let data = JSON.stringify({ message: 'Page is refreshing' });
    navigator.sendBeacon(`/api/streaming_logs?event=beforeunload`, data);
});

window.addEventListener('unload', function () {
    let data = JSON.stringify({ message: 'Page is closing' });
    navigator.sendBeacon(`/api/streaming_logs?event=unload`, data);
});

window.onload = function() {
    const hangoutButton = document.getElementById("searchButton");
    hangoutButton.click(); // this will trigger the click event
};