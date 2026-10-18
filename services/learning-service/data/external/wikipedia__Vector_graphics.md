<!-- role: Graphic Designer -->
<!-- topic: Graphic Design -->
<!-- source: Wikipedia (Wikipedia contributors) -->
<!-- license: CC BY-SA 4.0 -->
<!-- url: https://en.wikipedia.org/wiki/Vector_graphics -->
# Vector graphics

Vector graphics are a form of computer graphics in which visual images are created directly from geometric shapes defined on a Cartesian plane, such as points, lines, curves and polygons. The associated mechanisms may include vector display and printing hardware, vector data models and file formats, as well as the software based on these data models (especially graphic design software, computer-aided design, and geographic information systems). Vector graphics are an alternative to raster or bitmap graphics, with each having advantages and disadvantages in specific situations.
While vector hardware has largely disappeared in favor of raster-based monitors and printers, vector data and software continue to be widely used, especially when a high degree of geometric precision is required, and when complex information can be decomposed into simple geometric primitives. Thus, it is the preferred model for domains such as engineering, architecture, surveying, 3D rendering, and typography, but is entirely inappropriate for applications such as photography and remote sensing, where raster is more effective and efficient. Some application domains, such as geographic information systems (GIS) and graphic design, use both vector and raster graphics at times, depending on purpose.
Vector graphics are based on the mathematics of analytic or coordinate geometry, and is not related to other mathematical uses of the term vector. This can lead to some confusion in disciplines in which both meanings are used.

## Data model
The logical data model of vector graphics is based on the mathematics of coordinate geometry, in which shapes are defined as a set of points in a two- or three-dimensional cartesian coordinate system, as p = (x, y) or p = (x, y, z). Because almost all shapes consist of an infinite number of points, the vector model defines a limited set of geometric primitives that can be specified using a finite sample of salient points called vertices. For example, a square can be unambiguously defined by the locations of three of its four corners, from which the software can interpolate the connecting boundary lines and the interior space. Because it is a regular shape, a square could also be defined by the location of one corner, a size (width=height), and a rotation angle.
The fundamental geometric primitives are:

A single point.
A line segment, defined by two end points, allowing for a simple linear interpolation of the intervening line.
A polygonal chain or polyline, a connected set of line segments, defined by an ordered list of points.
A polygon, representing a region of space, defined by its boundary, a polyline with coincident starting and ending vertices.
A variety of more complex shapes may be supported:

Parametric curves, in which polylines or polygons are augmented with parameters to define a non-linear interpolation between vertices, including circular arcs, cubic splines, Catmull–Rom splines, Bézier curves and bezigons.
Standard parametric shapes in two or three dimensions, such as circles, ellipses, squares, superellipses, spheres, tetrahedrons, superellipsoids, etc.
Irregular three-dimensional surfaces and solids, are usually defined as a connected set of polygons (e.g., a polygon mesh) or as parametric surfaces (e.g., NURBS).
Fractals, often defined as an iterated function system.
In many vector datasets, each shape can be combined with a set of properties. The most common are visual characteristics, such as color, line weight, or dash pattern. In systems in which shapes represent real-world features, such as GIS and BIM, a variety of attributes of each represented feature can be stored, such as name, age, size, and so on.
In some Vector data, especially in GIS, information about topological relationships between objects may be represented in the data model, such as tracking the connections between road segments in a transport network.
If a dataset stored in one vector file format is converted to another file format that supports all the primitive objects used in that particular image, then the conversion can be lossless.

## Vector display hardware
Vector-based devices, such as the vector CRT and the pen plotter, directly control a drawing mechanism to produce geometric shapes. Since vector display devices can define a line by dealing with just two points (that is, the coordinates of each end of the line), the device can reduce the total amount of data it must deal with by organizing the image in terms of pairs of points.
Vector graphic displays were first used in 1958 by the US SAGE air defense system. Vector graphics systems were retired from the U.S. en route air traffic control in 1999. Vector graphics were also used on the TX-2 at the Massachusetts Institute of Technology Lincoln Laboratory by computer graphics pioneer Ivan Sutherland to run his program Sketchpad in 1963.
Subsequent vector graphics systems, most of which iterated through dynamically modifiable stored lists of drawing instructions, include the IBM 2250, Imlac PDS-1, and DEC GT40. There was a video game console that used vector graphics called Vectrex as well as various arcade games like Asteroids, Space Wars, Tempest and many cinematronics titles such as Rip Off, and Tail Gunner using vector monitors. Storage scope displays, such as the Tektronix 4014, could display vector images but not modify them without first erasing the display. However, these were never as widely used as the raster-based scanning displays used for television, and had largely disappeared by the mid-1980s except for specialized applications.
Plotters used in technical drawing still draw vectors directly to paper by moving a pen as directed through the two-dimensional space of the paper. However, as with monitors, these have largely been replaced by the wide-format printer that prints a raster image (which may be rendered from vector data).

## Software
Because this model is useful in a variety of application domains, many different software programs have been created for drawing, manipulating, and visualizing vector graphics. While these are all based on the same basic vector data model, they can interpret and structure shapes very differently, using very different file formats.

Graphic design and illustration, using a vector graphics editor or graphic art software such as Adobe Illustrator. See Comparison of vector graphics editors for capabilities.
Geographic information systems (GIS), which can represent a geographic feature by a combination of a vector shape and a set of attributes. GIS includes vector editing, mapping, and vector spatial analysis capabilities.
Computer-aided design (CAD), used in engineering, architecture, and surveying. Building information modeling (BIM) models add attributes to each shape, similar to a GIS.
3D computer graphics software, including computer animation.

## File formats
Vector graphics are commonly found today in the SVG, WMF, EPS, PDF, CDR or AI types of graphic file formats, and are intrinsically different from the more common raster graphics file formats such as JPEG,  PNG, APNG, GIF, WebP,  BMP and MPEG4.
The World Wide Web Consortium (W3C) standard for vector graphics is Scalable Vector Graphics (SVG). The standard is complex and has been relatively slow to be established at least in part owing to commercial interests. Many web browsers now have some support for rendering SVG data but full implementations of the standard are still comparatively rare.
In recent years, SVG has become a significant format that is completely independent of the resolution of the rendering device, typically a printer or display monitor. SVG files are essentially printable text that describes both straight and curved paths, as well as other attributes. Wikipedia prefers SVG for images such as simple maps, line illustrations, coats of arms, and flags, which generally are not like photographs or other continuous-tone images. Rendering SVG requires conversion to a raster format at a resolution appropriate for the current task. SVG is also a format for animated graphics.
There is also a version of SVG for mobile phones called SVGT (SVG Tiny version). These images can count links and also exploit anti-aliasing. They can also be displayed as wallpaper.
CAD software uses its own vector data formats, usually proprietary formats created by  software vendors, such as Autodesk's DWG and public exchange formats such as DXF. Hundreds of distinct  vector file formats have been created for GIS data over its history, including proprietary formats like the Esri file geodatabase, proprietary but public formats like the Shapefile and the original KML, open source formats like GeoJSON, and formats created by standards bodies like Simple Features and GML from the Open Geospatial Consortium.

### Conversion
### = To raster =
Modern displays and printers are raster devices; vector formats have to be converted to a raster format (bitmaps – pixel arrays) before they can be rendered (displayed or printed). The size of the bitmap/raster-format file generated by the conversion will depend on the resolution required, but the size of the vector file generating the bitmap/raster file will always remain the same. Thus, it is easy to convert from a vector file to a range of bitmap/raster file formats but it is much more difficult to go in the opposite direction, especially if subsequent editing of the vector picture is required. It might be an advantage to save an image created from a vector source file as a bitmap/raster format, because different systems have different (and incompatible) vector formats, and some might not support vector graphics at all. However, once a file is converted from the vector format, it is likely to be bigger, and it loses the advantage of scalability without loss of resolution. It will also no longer be possible to edit individual parts of the image as discrete objects. The file size of a vector graphic image depends on the number of graphic elements it contains; it is a list of descriptions.

### = From raster =
### Printing
Vector art is ideal for printing since the art is made from a series of mathematical curves; it will print very crisply even when resized. For instance, one can print a vector logo on a small sheet of copy paper, and then enlarge the same vector logo to billboard size and keep the same crisp quality. A low-resolution raster graphic would blur or pixelate excessively if it were enlarged from business card size to billboard size. (The precise resolution of a raster graphic necessary for high-quality results depends on the viewing distance; e.g., a billboard may still appear to be of high quality even at low resolution if the viewing distance is great enough.)
If we regard typographic characters as images, then the same considerations that we have made for graphics apply even to the composition of written text for printing (typesetting). Older character sets were stored as bitmaps. Therefore, to achieve maximum print quality they had to be used at a given resolution only; these font formats are said to be non-scalable. High-quality typography is nowadays based on character drawings (fonts) which are typically stored as vector graphics, and as such are scalable to any size. Examples of these vector formats for characters are Postscript fonts and TrueType fonts.

## Operation
Advantages of this style of drawing over raster graphics:

Because vector graphics consist of coordinates with lines/curves between them, the size of the representation does not depend on the dimensions of the object. This minimal amount of information translates to a much smaller file size compared to large raster images which are defined pixel by pixel. This said, a vector graphic with a small file size is often said to lack detail compared with a real-world photo.
Correspondingly, one can infinitely zoom in on e.g., a circle arc, and it remains smooth. On the other hand, a polygon representing a curve will reveal being not really curved.
On zooming in, lines and curves need not get wider proportionally. Often the width is either not increased or less than proportional. On the other hand, irregular curves represented by simple geometric shapes may be made proportionally wider when zooming in, to keep them looking smooth and not like these geometric shapes.
The parameters of objects are stored and can be later modified. This means that moving, scaling, rotating, filling, etc. does not degrade the quality of a drawing. Moreover, it is usual to specify the dimensions in device-independent units, which results in the best possible rasterization on raster devices.
From a 3-D perspective, rendering shadows is also much more realistic with vector graphics, as shadows can be abstracted into the rays of light from which they are formed. This allows for photorealistic images and renderings.
For example, consider a circle of radius r. The main pieces of information a program needs in order to draw this circle are

An indication that what is to be drawn is a circle
the radius r
the location of the center point of the circle
stroke line style and color (possibly transparent)
fill style and color (possibly transparent)
Vector formats are not always appropriate in graphics work and also have numerous disadvantages. For example, devices such as cameras and scanners produce essentially continuous-tone raster graphics that are impractical to convert into vectors, and so for this type of work, an image editor will operate on the pixels rather than on drawing objects defined by mathematical expressions. Comprehensive graphics tools will combine images from vector and raster sources, and may provide editing tools for both, since some parts of an image could come from a camera source, and others could have been drawn using vector tools.
Some authors have criticized the term vector graphics as being confusing. In particular, vector graphics does not simply refer to graphics described by Euclidean vectors. Some authors have proposed to use object-oriented graphics instead. However this term can also be confusing as it can be read as any kind of graphics implemented using object-oriented programming.

## Vector operations
Vector graphics editors typically allow translation, rotation, mirroring, stretching, skewing, affine transformations, changing of z-order (loosely, what's in front of what) and combination of primitives into more complex objects. More sophisticated transformations include set operations on closed shapes (union, difference, intersection, etc.). In SVG, the composition operations are based on alpha composition.
Vector graphics are ideal for simple or composite drawings that need to be device-independent, or do not need to achieve photo-realism. For example, the PostScript and PDF page description languages use a vector graphics model.

## Vector image repositories
Many stock photo websites provide vectorized versions of hosted images, while specific repositories specialize in vector images given their growing popularity among graphic designers.
