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
                colors: ['#222fb9', 'rgb(255, 122, 1)', '#21b731','#888282','#ff6175'],
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
                            label: "\xa0 \xa0 Auto Tickets \xa0 \xa0",
                            value: response.auto_tickets_count,
                        },
                        {
                            label: "\xa0 \xa0 Manual Tickets \xa0 \xa0",
                            value: response.manual_tickets_count,
                        }
                    ]);
                },
                error: function(error){
                    console.error('Error fetching data:', error);
                }
            });
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
