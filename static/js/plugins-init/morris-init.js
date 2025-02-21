(function($) {
    "use strict"

    var dzMorris = function(){
        var screenWidth = $(window).width();

        var setChartWidth = function(){
            if(screenWidth <= 768)
            {
                var chartBlockWidth = 0;
                chartBlockWidth = (screenWidth < 300 ) ? screenWidth : 300;
                jQuery('.morris_chart_height').css('min-width', chartBlockWidth - 31);
            }
        }

        var donutChart = function(data){
            Morris.Donut({
                element: 'morris_donught',
                data: data,
                resize: true,
                redraw: true,
                colors: ['#222fb9', 'rgb(255, 122, 1)', '#21b731', '#888282', '#ff6175'],
                labelColor: '#2e2e2e',  // Color of the labels
                formatter: function (x) { return x + "" },  // Format the label values
            });
        }

        // Function to fetch dynamic data from the server
        var fetchDynamicData = function(){
            $.ajax({
                url: '/get_ticket_datas/',  // URL to your Django view
                method: 'GET',
                dataType: 'json',
                success: function(response){
                    // Use the fetched data to populate the chart
                    donutChart([
                        {
                            label: "Auto Tickets",
                            value: response.auto_tickets_count,
                        },
                        {
                            label: "Manual Tickets",
                            value: response.manual_tickets_count,
                        }
                    ]);

                    // Display the data in a separate HTML element
                    displayData(response);
                },
                error: function(error){
                    console.error('Error fetching data:', error);
                }
            });
        }

// Function to display data in a separate HTML element
var displayData = function(response){
    var dataList = document.getElementById('data-list');
    if (dataList) {
        // Clear existing data
        dataList.innerHTML = '';

        // Add list items for each data point with different colors
        dataList.innerHTML += '<li><span style="color: #222fb9;">Auto Tickets:</span> ' + response.auto_tickets_count + '</li>';
        dataList.innerHTML += '<li><span style="color: rgb(255, 122, 1);">Manual Tickets:</span> ' + response.manual_tickets_count + '</li>';
    }
}

        /* Function ============ */
        return {
            init:function(){
                setChartWidth();
                fetchDynamicData();  // Fetch dynamic data and populate the chart
            },
        }
        
    }();

    jQuery(document).ready(function(){
        dzMorris.init();
    });

    // ...
})(jQuery);