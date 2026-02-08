# 2-GDAL学习


---

## 幻灯片 1

指 导 老 师：常学立

GDAL编程学习


---

## 幻灯片 2

CONTENTS

目录

其他算法

05


---

## 幻灯片 3

PART 01

GDAL基础介绍与学习目标

1


---

## 幻灯片 4

基础介绍

GDAL核心类结构设计

GDALMajorObject类：带有元数据的对象。

GDALDdataset类：通常是从一个栅格文件中提取的相关联的栅格波段集合和这些波段的元数据；GDALDdataset也负责所有栅格波段的地理坐标转换(georeferencingtransform)和坐标系定义。

GDALDriver类：文件格式驱动类，GDAL会为每一个所支持的文件格式创建一个该类的实体，来管理该文件格式。

GDALDriverManager类：文件格式驱动管理类，用来管理GDALDriver类


---

## 幻灯片 5

OGR体系结构

Geometry：类Geometry (包括OGRGeometry等类)封装了OpenGIS的矢量数据模型，并提供了一些几何操作，WKB(Well Knows Binary)和WKT(Well Known Text)格式之间的相互转换，以及空间参考系统(投影)。

Spatial Reference：类OGRSpatialReference封装了投影和基准面的定义。

Feature：类OGRFeature封装了一个完整feature的定义，一个完整的feature包括一个geometry和geometry的一系列属性。


---

## 幻灯片 6

OGR体系结构

Feature Definition：类OGRFeatureDefn里面封装了feature的属性，类型、名称及其默认的空间参考系统等。一个OGRFeatureDefn对象通常与一个层(layer)对应。

Layer：类OGRLayer是一个抽象基类，表示数据源类OGRDataSource里面的一层要素(feature)。

Data Source：类OGRDataSource是一个抽象基类，表示含有OGRLayer对象的一个文件或一个数据库。

Drivers：类OGRSFDriver对应于每一个所支持的矢量文件格式。类OGRSFDriver由类OGRSFDriverRegistrar来注册和管理。


---

## 幻灯片 7

OGR常用函数

Geometry(ogr_geometry)几何对象：几何对象类（OGRGeometry等）封装了OpenGIS模型矢量数据以及一些几何操作，并且提供常用的二进制格式和文本格式之间的转换。一个几何对象包含一个空间参考（即投影）。

Spatial Reference(ogr_specialref.h)空间参考：一个OGRSpatialReference对象定义了投影和水准面等信息。

Feature(ogr_feature.h)要素：OGRFeture类里面定义了一个完整的要素，由一个几何对象和一系列属性组成。


---

## 幻灯片 8

OGR常用函数

Feature Class Definition(ogr_feature.h)要素类定义：OGRFetureDefn类体现了一组相关要素的格式

Layer(ogrsf_frmts.h)图层：OGRLayer是一个抽象基类，用来描述一个在OGRData Source中的一个图层的所有要素

DataSource(ogrsf_frmts.h)数据源：OGRDataSource是一个抽象基类，用于表现一个文件或数据库，里面包含一个或多个OGRLayer对象

Drivers(ogrs_frmts.h)驱动：OGRSFDriver表示一个指定格式的转换器，打开文件返回一个OGRDataSource对象，所有支持的驱动使用OGRSFDriverRegistrar来进行管理。


---

## 幻灯片 9

学习目标

实现常用的影像读取

GDAL数据集、常用类

注册文件格式

图像的格式、大小、波段等

颜色表、图像统计信息

分块读写（重点）

格式转换

GeoTIFF格式

JPEG、PNG图像使用

MEM文件使用说明

利用创建RastIO( )函数

TIFF转为jepg浏览图

其他算法学习 (拓展)

图像重采样

图像镶嵌

图像裁切

图像重投影、图像校正

如影像读写8位、16位同时兼容

读写栅格文件如何消除差异


---

## 幻灯片 10

PART 02

影像信息读取

02


---

## 幻灯片 11

预备知识——数据集（由GDALDataset类表示）

数据集是一个栅格波段数据和所有相关信息的集合。

数据集有一个应用于所有波段的栅格大小的概念（由像素或者行表示）。

数据集也负责所有波段数据的地理投影转换和坐标定义的任务。


---

## 幻灯片 12

打开数据集

CString strFilePath;

StrFilePath=’d:/rsdata/2005_234.tif’;

GDALDataSet *poDataset; //GDAL数据集

GDALAllRegister();

poDataset = (GDALDataset *) GDALOpen(strFilePath, GA_ReadOnly );

数据（影像）操作的第一步就是打开一个数据集

对于一般的格式来说，一个“数据集”就是一个文件，比如一个TIFF文件就是一个以tiff为扩展名的文件

通过数据集poDataset即可调用各功能函数


---

## 幻灯片 13

调用功能函数

GetRasterCount();//获取图像波段数；

GetRasterXSize();//获取图像宽度

GetRasterYSize();//获取图像高度

GetRasterBand();//获取图像某一波段

GetGeoTransform(double *p);//获取图像地理坐标信息长度为六的数组

RasterIO();//对图像数据进行缩放读和写

通过数据集poDataset即可调用各功能函数

获取图像波段数、宽度高度、波段等信息


---

## 幻灯片 14

获取基本信息

int  nBandCount=poDataset->GetRasterCount();

int  nImgSizeX=poDataset->GetRasterXSize();

int  nImgSizeY=poDataset->GetRasterYSize();

double  adfGeoTransform[6];

poDataset->GetGeoTransform( adfGeoTransform );

一般情况下我们需要得到图像的高、宽、波段数、地理坐标信息，数据类型等；

如果图像不含地理坐标信息，默认返回值是：（0、1、0、0、0、1）


---

## 幻灯片 15

类的封装（拓展）

类的封装——8位、16位的图像读写差异

创建栅格文件

读、写栅格文件


---

## 幻灯片 16

PART 02

影像信息读取实例

02


---

## 幻灯片 17

获取基本信息

01

02

02

裁剪lena图像的某部分内容

将其放入到新创建的.tif文件


---

## 幻灯片 18

获取基本信息

01.打开图像

指的是获取图像的头文件，以此得到图像的一些信息，没有涉及到读取像素操作。

02.读取图像信息

图像宽、高总所周知了，而波段数就是通道，如RGB图像的波段数为3。深度标识的就是图像的存储单位，比如一般图像就是8位，用无字节字符型unsigned char来表达0~255的像素值；而除以8标识1个字节，方便读取像素buf。

03.关闭打开的文件

如果已经读取完毕或者不需要这张图像的相关操作了，最后要关闭打开的文件，否则会内存泄漏。


---

## 幻灯片 19

创建图像

01.创建图像

这里创建了一个256X256大小,被读取图像波段，深度8位的tif

02.参数的设置

需要注意的是创建图像可能需要一些特别的设置信息，是需要到GDAL对应格式的文档中去查看的，也可以什么都不设置用默认值。我这里设置的是如果需要的话，就创建支持大小超过4G的bigtiff。

03.关闭打开的文件

如果已经写入完毕或者不需要这张图像的相关操作了，最后一定要注意关闭关闭打开的文件，之前只会内存泄漏，而这里还会可能创建失败。

04.创建后位操作

如果创建后什么都不做，关闭后GDAL会自动写入0像素值，打开后就是纯黑色图像。


---

## 幻灯片 20

创建图像

01.创建图像

这里创建了一个256X256大小,被读取图像波段，深度8位的tif

02.参数的设置

需要注意的是创建图像可能需要一些特别的设置信息，是需要到GDAL对应格式的文档中去查看的，也可以什么都不设置用默认值。我这里设置的是如果需要的话，就创建支持大小超过4G的bigtiff。

03.关闭打开的文件

如果已经写入完毕或者不需要这张图像的相关操作了，最后一定要注意关闭关闭打开的文件，之前只会内存泄漏，而这里还会可能创建失败。

04.创建后位操作

如果创建后什么都不做，关闭后GDAL会自动写入0像素值，打开后就是纯黑色图像。


---

## 幻灯片 21

PART 03

GDAL生成快视图

03


---

## 幻灯片 22

引言

为什么需要快视图？

在进行遥感数据平台建设时，往往需要在查看原始数据时查看数据缩略图来确保数据云量是否满足要求（往往是遥感图像太大，不可以快速显示，所以拿缩略图来辅助审查）。


---

## 幻灯片 23

常用方法

第一种利用重采样生产小图像。

第二种将生成的小图像CreateCopy生成jpg格式或者png格式。（本实例介绍的内容）

注意：由于GDAL不支持直接创建jpg或者png的压缩格式的图像，所以中间需要一个中转的过程（MEM文件）。关于MEM内存文件的使用，和普通的图像一样，只不过在创建的时候（上一节已经给出实例），驱动选择MEM，创建图像的时候不需要指定文件路径，直接用空字符串即可。


---

## 幻灯片 24

生成浏览图

常见问题

借助MEM内存创建

利用C\C++ 函数创建

解决方法

拉伸图像：借用RasterIO函数或者其他线性、分段拉伸等

解决方案

Jepg只能存储8位图像


---

## 幻灯片 25

判断图像格式

char* findImageTypeGDAL( char *pDstImgFileName)

{

char *dstExtension = strlwr(strrchr(pDstImgFileName,'.') + 1);

char *Gtype = NULL;

if (0 == strcmp(dstExtension,"bmp")) Gtype = "BMP";

else if (0 == strcmp(dstExtension,"jpg")) Gtype = "JPEG";

else if (0 == strcmp(dstExtension,"png")) Gtype = "PNG";

else if (0 == strcmp(dstExtension,"tif")) Gtype = "GTiff";

else if (0 == strcmp(dstExtension,"gif")) Gtype = "GIF";

else Gtype = NULL;

return Gtype;

}

根据文件后缀名判断图像格式


---

## 幻灯片 26

实例步骤

S

W

O

步骤1

读取原始图像的数据，返回图像的宽、高、通道数量

步骤2

创建MEM内存驱动器，将原始图像的数据写入到内存驱动器中。

步骤3

读取和写入的时候，都是按通道从0 0位置开始一次性读取图像宽和高数量的像素。

按照源图像的通道数量作为间隔拷贝原始数据到内存驱动器中。

参考代码：https://blog.csdn.net/weixin_44231643/article/details/85629525?utm_medium=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.edu_weight&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.edu_weight


---

## 幻灯片 27

PART 04

分块读写

04


---

## 幻灯片 28

引言1

为什么需要分块读写？

遥感影像小则几百兆，大则5、6GB，所以在使用GDAL进行图像读取时面临读写速度较慢的问题，常用的方式是借用GDAL中RasterIO函数的机制。


---

## 幻灯片 29

引言2

为什么使用RasterIO函数？

RasterIO（）函数能够对图像任意指定区域任意波段的数据按指定数据类型，指定排列方式读入内存和写入文件中，因此可以实现对大影像的分块读，运算，写操作。

对于大图像处理，按照传统方法，首先要将图像所有数据读入内存中，进行相应操作后，再一次性将处理好的数据写入文件中，这样需要耗费很大内存，容易内存溢出，而且存续可执行行差。

采用分块处理技术，一幅1G的影像，在整个数据处理过程中，可以只占用几十兆的内存，而且运算量不会增加。


---

## 幻灯片 30

两类RasterIO()函数（以GDALDataset中的为例）

CPLErr GDALDataset::RasterIO    (   GDALRWFlag eRWFlag,

int     nXOff,

int     nYOff,

int     nXSize,

int     nYSize,

void * pData,

int     nBufXSize,

int     nBufYSize,

GDALDataType    eBufType,

int     nBandCount,

int *   panBandMap,

int     nPixelSpace,

int     nLineSpace,

int     nBandSpace

)

参数1：读写标记。如果为GF_Read，则是将影像内容写入内存，如果为GF_Write，则是将内存中内容写入文件。

参数2、3：读写开始位置。相对于图像左上角顶点(从零开始)的行列偏移量。

参数4、5：要读写的块在x方向的象素个数和y方向的象素列数。

参数6：指向目标缓冲区的指针，由用户分配。

参数7、8：目标块在x方向上和y方向上的大小。

参数9：目标缓冲区的数据类型，原类型会自动转换为目标类型。

参数10：要处理的波段数。

参数11：记录要操作的波段的索引(波段索引从1开始)的数组，若为空则数组中存放的是前nBandCount个波段的索引。

参数12：X方向上两个相邻象素之间的字节偏移，默认为0，则列间的实际字节偏移由目标数据类型eBufType确定。

参数13：y方向上相邻两行之间的字节偏移, 默认为0，则行间的实际字节偏移为eBufType * nBufXSize。

参数14：相邻两波段之间的字节偏移，默认为0,则意味着波段是顺序结构的，其间字节偏移为nLineSpace * nBufYSize。


---

## 幻灯片 31

两类RasterIO()函数（以GDALDataset中的为例）

int panBandMap [3]= {3,2,1};   //按照BGR BGR BGR ... 来读取数据组织

DT_8U *pData = new DT_8U[iWidth*iHeight*3];

poDataset ->RasterIO(GF_Read, 0, 0, iWidth,iHeight, pData,iWidth, iHeight,        (GDALDataType)iDataType, 3, panBandMap,iDataType*3, iDataType*iMthWidth*3, iDataType);

在Windsow位图数据颜色排列是BGR，但是图像存储的可能是按照RGB来存储的，一般的做法是将数据按照每个波段读出来，然后再认为的按照BGR来进行组织，其实完全可以使用后面三个参数来将读出来的数据自动按照BGR的方式组织好。只要将参数设置为：nBandCount=3;panBandMap =new int[]{3,2,1}即可。


---

## 幻灯片 32

分块读写实例1

01

02

02

读取起点位置开始的256X256的内容

读取特定波段

03

04

左下角起点读写

重采样读写


---

## 幻灯片 33

读取起点位置开始的256X256的内容

步骤1：申请buf

步骤2：读取图像

步骤3：写入

步骤4：释放内存


---

## 幻灯片 34

16位影像读写

与实例1相比，除了要更改buf的容量和RasterIO()的第九个参数GDT_UInt16，其余什么都不需要更改。

注意：创建16位图像时参数也需要更改成16位。


---

## 幻灯片 35

读取特定波段

结果如右图所示

某些情况下需要读取特定波段，或者需要重组波段顺序。


---

## 幻灯片 36

左下角起点读写

默认情况RasterIO()是以左上角起点读写的，不过也是可以以左下角为起点读写，只需要重新设置排布buf的位置。这里读写lena图像上同一块位置。

注意：这里Y方向起点位置，也就是第三个参数仍然要用左上角起算，但是buf已经是左下角起点了。


---

## 幻灯片 37

重采样读写

RasterIO()另外一个用法是可以自动缩放，重采样读写影像，例如这里将512X512大小的lena图像重采样成256X256大小。

可以看到重采样读写只需要修改参数4，参数5就行了。

RasterIO()重采样方式默认是最临近的方法（其他方法可以自行学习），只有建立金字塔时可以设置重采样方式，但也仅限于缩小。


---

## 幻灯片 38

对大图像进行分块操作

参考代码：

https://blog.csdn.net/liminlu0314/article/details/73881097?ops_request_misc=%257B%2522request%255Fid%2522%253A%2522159427285519725222453256%2522%252C%2522scm%2522%253A%252220140713.130102334..%2522%257D&request_id=159427285519725222453256&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~first_rank_ecpm_v3~pc_rank_v3-3-73881097.pc_ecpm_v3_pc_rank_v3&utm_term=gdal%E8%AF%BB%E5%86%99%E5%9B%BE%E5%83%8F%E5%88%86%E5%9D%97%E5%A4%84%E7%90%86


---

## 幻灯片 39

PART 04

其他算法

05


---

## 幻灯片 40

图像重采样

图像镶嵌

重要算法

图像重投影、图像校正

图像裁切

RasterIO 函数

GDALWarp 类

GDALWarp 类提供的相应接口

矩形的规则裁切

AOI的不规则裁切

坐标转换

数学关系


---

## 幻灯片 41

THANKS

感谢聆听
