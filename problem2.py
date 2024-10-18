import xarray as xr
import numpy as np
from PIL import Image
import imageio.v2 as imageio
import pygmt
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QSlider, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class EarthElevationVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        
        self.setWindowTitle("Earth Elevation Visualiser - Educational Visualisation")
        self.setGeometry(100, 100, 800, 600)

        self.region_to_plot = [-180, 180, -90, 90]
        self.output_path = "./output_plot.png"
        self.perspective = [-120, 30]
        self.contour_interval = 250

        self.grid = pygmt.datasets.load_earth_relief(resolution="10m", region=self.region_to_plot)
        self.color_map = self.load_color_map()
        self.displacement_map = self.load_displacement_map()

        # general setup for the window
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.graphics_view = QGraphicsView(self)
        layout.addWidget(self.graphics_view)

        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)

        # pixmap item to hold the map image
        self.map_item = QGraphicsPixmapItem()
        self.scene.addItem(self.map_item)

        # set up the initial global map
        self.show_global_map()

        # buttons for visualization techniques
        btn_global_map = QPushButton("Global Map", self)
        btn_3d_perspective = QPushButton("3D Perspective", self)
        btn_isocontours = QPushButton("Isocontours", self)
        layout.addWidget(btn_global_map)
        layout.addWidget(btn_3d_perspective)
        layout.addWidget(btn_isocontours)

        self.label_slider_value = QLabel(f"Change Perspective:", self)
        layout.addWidget(self.label_slider_value)

        self.slider_perspective = QSlider(Qt.Horizontal)
        self.slider_perspective.setMinimum(-180)
        self.slider_perspective.setMaximum(180)
        self.slider_perspective.setValue(self.perspective[0])
        layout.addWidget(self.slider_perspective)
        self.slider_perspective.sliderReleased.connect(self.update_perspective)

        # slider for contour values
        self.label_contour_value = QLabel(f"Change Contour Interval:", self)
        layout.addWidget(self.label_contour_value)

        self.slider_contour = QSlider(Qt.Horizontal)
        self.slider_contour.setMinimum(100)
        self.slider_contour.setMaximum(2000)
        self.slider_contour.setValue(self.contour_interval)
        layout.addWidget(self.slider_contour)
        self.slider_contour.sliderReleased.connect(self.adjust_contour_interval)

        # connect widgets to functions
        btn_global_map.clicked.connect(self.show_global_map)
        btn_3d_perspective.clicked.connect(self.plot_3d_pespective)
        btn_isocontours.clicked.connect(self.show_isocontours)
    
        # zoom functionality
        self.graphics_view.wheelEvent = self.zoom_event

        # mouse events
        self.graphics_view.mousePressEvent = self.mouse_press_event
    
    def load_color_map(self):
            
        image_path = "./dataset_vis/dataset/colour_dataset/8081_earthmap2k.jpg" 
        image = Image.open(image_path)

        rgb_array = np.array(image)

        latitudes = np.linspace(90, -90, rgb_array.shape[0])
        longitudes = np.linspace(-180, 180, rgb_array.shape[1])

        data_array = xr.DataArray(rgb_array, dims=('latitude', 'longitude', 'channel'),coords={'latitude': latitudes,'longitude': longitudes,'channel': ['red', 'green', 'blue']})

        data_array = data_array.transpose('channel', 'latitude', 'longitude')

        return data_array
    
    def load_displacement_map(self):
        displacement_map_file = "./dataset_vis/dataset/displacement_dataset/8081_earthbump10k.jpg"

        # read displacement map image
        bumpmap = imageio.imread(displacement_map_file)

        # scale the data values to the range [0, 4000]
        min_value = 0
        max_value = 4000
        scaled_image = min_value + ((max_value - min_value) / 255.0) * bumpmap

        height, width = scaled_image.shape

        # create latitude and longitude values
        latitudes = np.linspace(90, -90, height)
        longitudes = np.linspace(-180, 180, width)

        # create an xarray.DataArray from the scaled image data with latitude and longitude coordinates
        bump_array = xr.DataArray(scaled_image, coords=[("lat", latitudes),("lon", longitudes)], dims=["lat", "lon"])

        return bump_array

    def show_global_map(self):
        self.plot( "./output_plot.png", "W6i", [-180, 180, -90, 90])
        self.display("./output_plot.png")

    def plot_3d_pespective(self):
        print("3D Perspective Visualization Selected")
        output_path = self.output_path
        region_to_plot = self.region_to_plot
        perspective = self.perspective

        grid = pygmt.datasets.load_earth_relief(resolution="10m", region=region_to_plot)
        # grid = self.displacement_map

        frame =  ["xa1f0.25","ya1f0.25", "z2000+lmeters", "wSEnZ"]

        pygmt.makecpt(
                cmap='geo',
                series=f'-6000/4000/100',
                continuous=True
            )

        fig = pygmt.Figure()
        fig.grdview(
            grid=grid,
            region=region_to_plot + [-6000, 4000],
            perspective=perspective,
            frame=frame,
            projection="M15c",
            zsize="4c",
            surftype="i",
            shading=True,
            cmap = "geo",
            contourpen="0.1p",
            
        )

        # fig.grdcontour(grid=pygmt.grdclip(grid, below=[1, 0]), annotation="500", interval=self.contour_interval, limit="z+", perspective=perspective)
        fig.basemap(
            perspective=True,
            rose="jTL+w3c+l+o-2c/-1c" #map directional rose at the top left corner 
        )

        fig.colorbar(perspective=True, frame=["a2000", "x+l'Elevation in (m)'", "y+lm"])
        fig.savefig(output_path, crop=True, dpi=300)
        self.display(output_path)

    def show_isocontours(self):
        grid = pygmt.datasets.load_earth_relief( resolution="10m", region = self.region_to_plot)

        fig = pygmt.Figure()

        fig.grdimage(
            grid=grid,
            cmap="geo",
            projection="Cyl_stere/30/-20/12c",
            frame=True,
            region=self.region_to_plot,
        )
        # create the contour plot
        fig.grdcontour(
            grid=grid,
            interval=self.contour_interval,
            annotation=1000,
            frame="a",
            projection="Cyl_stere/30/-20/12c",
            region=self.region_to_plot,
        )

        # fig.colorbar(frame=["x+lelevation", "y+lm"])
        # show the plot
        fig.savefig(self.output_path)
        self.display(self.output_path)
        print("Isocontours Visualization Selected")


    def zoom_event(self, event):
        factor = 1.2
        if event.angleDelta().y() < 0:
            factor = 1.0 / factor
        self.graphics_view.scale(factor, factor)
    
    def display(self, output_path):
        pixmap = QPixmap(output_path)
        self.map_item.setPixmap(pixmap)

    def plot(self, output_path, projection, region_to_plot):
        # grid = pygmt.datasets.load_earth_relief(resolution="10m", region= region_to_plot)
        grid = self.color_map
        fig = pygmt.Figure()
        fig.grdimage(grid=grid, cmap="geo", projection=projection, region = region_to_plot, frame=True)
        fig.savefig(output_path)

    def plot_image(self, output_path, projection, region_to_plot):
        grid = pygmt.datasets.load_earth_relief(resolution="10m", region= region_to_plot)
    
        fig = pygmt.Figure()
        fig.grdimage(grid, cmap="geo", projection=projection, region = region_to_plot, shading=True, frame=True)
        fig.savefig(output_path)

    def mouse_press_event(self, event):
        pos = event.pos()
        scene_pos = self.graphics_view.mapToScene(pos)
        x,y = scene_pos.x(), scene_pos.y()

        print(f"Clicked Position: {x}, {y}")
        # print(f"grid.shape: {self.grid.shape}")
        # assuming self.grid.shape is (height, width)
        # get the height and width of the window
        height, width = self.grid.shape
        height -= 180
        width -= 360

        # print(f"height: {height}, width: {width}")

        # convert the clicked position to a latitude and longitude
        lon = x / width * 360.0 - 180.0
        lat = 90.0 - y / height * 180.0


        # sample the height at the clicked position
        sampled_height = self.sample_height(lon, lat)

        print(f"Sampled Height at Lon: {lon}, Lat: {lat} - Height: {sampled_height}")

        # handle click event
        #if clicked on Africa show Africa
        if lon >= -20 and lon <= 60 and lat >= -40 and lat <= 40:
            self.plot_continent("./africa.png", [-20, 60, -40, 40], "AF", "africa_info.png")
            self.display("./africa.png")

        #if clicked on Europe show Europe
        elif lon >= -10 and lon <= 40 and lat >= 30 and lat <= 70:
            self.plot_continent("./europe.png", [-10, 40, 30, 70], "EU", "europe_info.png")
            self.display("./europe.png")
        
        #if clicked on Asia show Asia
        elif lon >= 60 and lon <= 150 and lat >= 0 and lat <= 60:
            self.plot_continent("./asia.png", [60, 150, 0, 60], "AS", "asia_info.png")
            self.display("./asia.png")
        
        #if clicked on North America show North America
        elif lon >= -170 and lon <= -50 and lat >= 10 and lat <= 80:
            self.plot_continent("./north_america.png", [-170, -50, 10, 80], "NA", "north_america_info.png")
            self.display("./north_america.png")

        #if clicked on South America show South America
        elif lon >= -90 and lon <= -30 and lat >= -60 and lat <= 20:
            self.plot_continent("./south_america.png", [-90, -30, -60, 20], "SA", "south_america_info.png")
            self.display("./south_america.png")

        #if clicked on Australia show Australia
        elif lon >= 100 and lon <= 160 and lat >= -50 and lat <= -10:
            self.plot_continent("./australia.png", [100, 160, -50, -10], "AU", "australia_info.png")
            self.display("./australia.png")

        #if clicked on Antarctica show Antarctica
        elif lon >= -180 and lon <= 180 and lat >= -90 and lat <= -60:
            self.plot_continent("./antarctica.png", [-180, 180, -90, -60], "AN", "antarctica_info.png")
            self.display("./antarctica.png")

    def plot_continent(self, output_path, region_to_plot, continent_code, info_file):
        fig = pygmt.Figure()

        fig.image(imagefile = info_file)

        fig.shift_origin(yshift="-2*h-1c")

        fig.coast( region="d", projection="H10c", land="gray", water="white", frame="afg", dcw=[ "="+continent_code+"+gred3" ] )

        fig.shift_origin(xshift="w+3c")   
        grid = pygmt.datasets.load_earth_relief(resolution="10m", region= region_to_plot)
        fig.grdimage(grid, cmap="geo", projection="Cyl_stere/30/-20/12c", region = region_to_plot, shading=True, frame=True)
        self.output_path = output_path
        self.region_to_plot = region_to_plot

        fig.savefig(output_path)
        

    def sample_height(self, lon, lat):
        sampled_height = self.grid[int(lat),int(lon)].values

        return sampled_height
    
    def update_perspective(self):
        # Update the perspective based on the slider value
        self.perspective[0] = self.slider_perspective.value()

        self.plot_3d_pespective()

    def adjust_contour_interval(self):
        # Update the contour interval based on the slider value
        self.contour_interval = self.slider_contour.value()

        self.show_isocontours()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EarthElevationVisualizer()
    window.show()
    sys.exit(app.exec_())