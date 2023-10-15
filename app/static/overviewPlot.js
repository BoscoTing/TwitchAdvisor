<<<<<<< Updated upstream
=======
let option = 'Average Message Count' // set default option 'Average Message Count'

currentDate = new Date();
startDate = new Date(currentDate.getFullYear(), 0, 1);
var days = Math.floor((currentDate - startDate) /
    (24 * 60 * 60 * 1000));

let week = Math.ceil(days / 7); // calculate week of year
let year = null;

>>>>>>> Stashed changes
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
                title: `Overview of ${option} at Week ${week}`,
                font: {
                    family: 'Verdana',
                    size: 15,
                },
                xaxis: {
                    // title: 'Weekdays'
                },
                yaxis: {
                    title: option
                },
                // barmode: 'group'
            };

            // Create the chart
            Plotly.react('overviewPlot', traces, layout);
        }
    };
    xmlHttp.send();
}


<<<<<<< Updated upstream
updateOverviewPlot();


=======
>>>>>>> Stashed changes
// add event listener on week selector of html.
function handleWeekSelection() {

    const weekInput = document.getElementById("week");
    const selectedWeek = weekInput.value;
    console.log("selectedWeek:", selectedWeek);
    const regex = /(\d+)-W(\d+)/;
    const match = selectedWeek.match(regex);
    if (match) {
        year = match[1];
        week = match[2];
        console.log(`Year: ${year}, Week: ${week}`);
        updateOverviewPlot(week, year);
    } else {
        console.log('No match found.');
    };
}

const overviewMetricsElements = document.getElementsByClassName("overviewMetrics")
for (var i = 0; i < overviewMetricsElements.length; i++) {
    let overviewMetricsElement = overviewMetricsElements[i];
    overviewMetricsElement.addEventListener ("click", function () {
        option = overviewMetricsElement.textContent;
        updateOverviewPlot(week, year);
    })
}


updateOverviewPlot();