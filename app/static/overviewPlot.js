let option = 'Average Message Count' // set default option 'Average Message Count'

function updateOverviewPlot(selectedWeek, selectedYear) {
    const loadingOverlay = document.getElementById("loadingOverlayOverview");
    loadingOverlay.style.display = "block";
    
    var xmlHttp = new XMLHttpRequest();
    if (selectedWeek && selectedYear) {
        xmlHttp.open( "GET", `/api/overview_data?week=${selectedWeek}&year=${selectedYear}`, true );
        console.log("GET", `/api/overview_data?week=${selectedWeek}&year=${selectedYear}`);
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
            const weekdays = ['Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.'];

            // Create data traces for each channel
            const traces = channels.map(channel => {
                const channelData = data.filter(entry => entry.channel === channel);
                const xValues = weekdays;
                const yValues = weekdays.map(weekday => {
                    const entry = channelData.find(dataEntry => dataEntry.weekDayName === weekday);
                    console.log(entry);
                    if (entry) {
                        console.log("entry: ", entry)
                    };

                    if (option == 'Average Message Count') {
                        return entry ? entry.avgMessageCount : 0;
                    }
                    else if (option == 'Max Message Count') {
                        return entry ? entry.maxMessageCount : 0;
                    }
                    else if (option == 'Average Sentiment Score') {
                        return entry ? entry.avgSentimentScore : 0;
                    }

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
                font: {
                    family: 'Verdana',
                    size: 15,
                },
                xaxis: {
                    // title: 'Weekdays'
                },
                yaxis: {
                    title: 'Average Message Count'
                },
                // barmode: 'group'
            };

            Plotly.react('overviewPlot', traces, layout);
        }
    };
    xmlHttp.send();
}


updateOverviewPlot();

// add event listener on week selector of html.
function handleWeekSelection() {

    const weekInput = document.getElementById("week");
    const selectedWeek = weekInput.value;
    console.log("selectedWeek:", selectedWeek);
    const regex = /(\d+)-W(\d+)/;
    const match = selectedWeek.match(regex);
    if (match) {
        const year = match[1];
        const week = match[2];
        console.log(`Year: ${year}, Week: ${week}`);
        updateOverviewPlot(week, year);
    } else {
        console.log('No match found.');
    };
    
}


// const weekOptions = document.getElementsByClassName("weekOptions")
// for (var i = 0; i < weekOptions.length; i++) {
//     let weekOption = weekOptions[i];
//     weekOption.addEventListener("click", function () {

//         const weekText = weekOption.textContent;
//         const match = weekText.match(/\d+/);
//         if (match) {
//             // Extracted week number
//             const selectedWeek = match[0];
//             console.log('selectedWeek:', selectedWeek);
//             updateOverviewPlot(selectedWeek, null);
//         } else {
//             console.log('Week number not found in text:', weekText);
//         };
//     });
// };