// Produce reference assets; dimensions are an experimental layout, not CAD data.
#include <opencv2/objdetect/aruco_detector.hpp>
#include <opencv2/imgcodecs.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
int main(int argc,char** argv) {
    if(argc!=2) { std::cerr<<"Usage: generate_board_reference NEW_DIRECTORY\n"; return 2; }
    try {
        std::filesystem::path out(argv[1]);
        if(!std::filesystem::create_directory(out)) throw std::runtime_error("Output exists");
        const auto dictionary=cv::aruco::getPredefinedDictionary(cv::aruco::DICT_4X4_50);
        cv::FileStorage fs((out/"layout.json").string(),cv::FileStorage::WRITE|cv::FileStorage::FORMAT_JSON);
        fs<<"schema"<<1<<"dictionary"<<"DICT_4X4_50"<<"orientation"<<"a8_top_left"<<"rectified_size"<<800;
        fs<<"provenance"<<"experimental simulated 280mm board; measure real installation";
        fs<<"board_side_mm"<<280.0<<"marker_black_side_mm"<<40.0<<"marker_white_margin_mm"<<4.0;
        fs<<"max_reprojection_error_rectified_px"<<5.0<<"markers"<<"[";
        const float centers[4][2]={{-120,-80},{400,-80},{400,280},{-220,280}};
        for(int id=0;id<4;++id) {
            cv::Mat marker; cv::aruco::generateImageMarker(dictionary,id,600,marker);
            cv::Mat page(720,720,CV_8U,cv::Scalar(255));
            marker.copyTo(page(cv::Rect(60,60,600,600)));
            if(!cv::imwrite((out/("marker-"+std::to_string(id)+".png")).string(),page)) throw std::runtime_error("PNG write failed");
            // SVG has physical size: print at 100%, black square 40mm, total 48mm.
            std::ofstream svg(out/("marker-"+std::to_string(id)+".svg"));
            svg<<"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"48mm\" height=\"48mm\" viewBox=\"0 0 720 720\"><rect width=\"720\" height=\"720\" fill=\"white\"/>";
            for(int r=0;r<6;++r) for(int c=0;c<6;++c) if(marker.at<unsigned char>(r*100+50,c*100+50)==0)
                svg<<"<rect x=\""<<60+c*100<<"\" y=\""<<60+r*100<<"\" width=\"100\" height=\"100\" fill=\"black\"/>";
            svg<<"</svg>";
            fs<<"{"<<"id"<<id<<"corners_rectified_px"<<"[";
            const float offsets[4][2]={{-20,-20},{20,-20},{20,20},{-20,20}};
            for(auto& d:offsets) fs<<"["<<(centers[id][0]+d[0])*800/280<<(centers[id][1]+d[1])*800/280<<"]";
            fs<<"]"<<"}";
        }
        fs<<"]";
        return 0;
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 2; }
}
