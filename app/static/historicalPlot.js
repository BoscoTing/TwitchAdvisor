function updateHistoricalPlot(selectBroadcaster) {
    var xmlHttp = new XMLHttpRequest();
    // selectBroadcaster = document.getElementsByClassName("defaultBroadcasters").value;
    // var host = window.location.host; 
    xmlHttp.open( "GET", `/api/historical_data?channel=${selectBroadcaster}`, false ); // false for synchronous request
    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            var responseHtml = xmlHttp.responseText;
            // console.log(responseHtml);
            var responseJson = JSON.parse(responseHtml);
            console.log(responseJson)
            let shedule = responseJson.shedule; // get the values of started_at
            console.log(shedule)
            let stats = responseJson.stats; // get the stats data
            const channel = stats.channel;
            // const cheers = stats.cheers;
            const startedAt = stats.started_at;
            const timestamp = stats.map(stats => new Date(stats.timestamp*1000));
            const avgViewerCount = stats.map(stats => stats.metadata.avg_viewer_count);
            const messageCount = stats.map(stats => stats.metadata.message_count);
            const chatterCount = stats.map(stats => stats.metadata.chatter_count);
            const cheer = stats.map(stats => stats.metadata.cheers.length);
            console.log(cheer)

            // document.querySelector("h1").textContent = `All user count: ${allUserCount}`;
            // document.querySelector("#view_info").setAttribute("data", JSON.stringify(viewInfoCount));
            // document.querySelector("#user_info").setAttribute("data", JSON.stringify(userInfoCount));

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
            
            Plotly.newPlot(
                    'historicalPlot', 
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

const defaultBroadcasters = document.getElementsByClassName("defaultBroadcasters")
for (var i = 0; i < defaultBroadcasters.length; i++) {
    let defaultBroadcaster = defaultBroadcasters[i]
    defaultBroadcaster.addEventListener("click", function () {
        selectBroadcaster = defaultBroadcaster.textContent;
        console.log(selectBroadcaster);
        updateHistoricalPlot(selectBroadcaster);
    });
};