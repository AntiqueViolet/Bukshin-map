ymaps.ready(function () {
    fetch('open_with_2gis.json')
        .then(response => response.json())
        .then(openData => {
            console.log("Данные загружены");

            const searchControls = new ymaps.control.SearchControl({
                options: {
                    float: 'right',
                    noPlacemark: true
                }
            });

            const myMap = new ymaps.Map("map", {
                center: [55.76, 37.64],
                zoom: 7,
                controls: [searchControls]
            });

            ['geolocationControl', 'trafficControl', 'fullscreenControl', 
             'zoomControl', 'rulerControl', 'typeSelector'].forEach(
                control => myMap.controls.remove(control)
            );

            const objectManager = new ymaps.ObjectManager({
                clusterize: true,
                clusterIconLayout: "default#pieChart",
                clusterDisableClickZoom: true
            });

            // Упрощенный дизайн точек - цвет зависит от in2gis
            objectManager.objects.setObjectOptions({
                preset: 'islands#circleIcon',
                iconColor: function(object) {
                    // Оранжевый для in2gis=true, синий для остальных
                    return object.properties.in2gis ? '#ff9a00' : '#1e98ff';
                },
                iconGlyph: function(object) {
                    // Символы для статуса in2gis
                    return object.properties.in2gis ? '✓' : '✕';
                },
                iconGlyphColor: '#fff',
                iconGlyphSize: 14
            });

            // Рассчитываем границы карты и преобразуем координаты
            let minLat = Infinity, maxLat = -Infinity;
            let minLon = Infinity, maxLon = -Infinity;
            
            openData.features.forEach(feature => {
                const coords = feature.geometry.coordinates;
                const [lon, lat] = coords;
                feature.geometry.coordinates = [lat, lon];
                
                minLat = Math.min(minLat, lat);
                maxLat = Math.max(maxLat, lat);
                minLon = Math.min(minLon, lon);
                maxLon = Math.max(maxLon, lon);
            });

            objectManager.add(openData);
            myMap.geoObjects.add(objectManager);

            if (isFinite(minLat)) {
                myMap.setBounds([[minLat, minLon], [maxLat, maxLon]], {
                    checkZoomRange: true
                });
            }
        })
        .catch(error => {
            console.error("Ошибка загрузки данных:", error);
            const myMap = new ymaps.Map("map", {
                center: [55.76, 37.64],
                zoom: 7
            });
        });
});