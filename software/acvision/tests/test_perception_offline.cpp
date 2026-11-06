#include <gtest/gtest.h>
#include "../apps/perception_offline.hpp"
#include <limits>

TEST(OfflinePerception, RejectsInvalidMatrices) {
    EXPECT_EQ(ac::offline::inputError({}),"EMPTY_OR_UNDECODABLE_IMAGE");
    EXPECT_EQ(ac::offline::inputError(cv::Mat(20,20,CV_8UC3)),"INVALID_DIMENSIONS");
    EXPECT_EQ(ac::offline::inputError(cv::Mat(30,30,CV_8UC1)),"UNSUPPORTED_CHANNELS");
    EXPECT_EQ(ac::offline::inputError(cv::Mat(30,30,CV_8UC4)),"UNSUPPORTED_CHANNELS");
    EXPECT_EQ(ac::offline::inputError(cv::Mat(30,30,CV_32FC3)),"UNSUPPORTED_DEPTH");
}

TEST(OfflinePerception, RejectsDegenerateCorners) {
    using Corners=std::array<cv::Point2f,4>;
    const Corners good{{{10,10},{90,10},{90,90},{10,90}}};
    EXPECT_TRUE(ac::offline::cornerError(good,{100,100}).empty());
    auto points=good;
    points[1]=points[0];
    EXPECT_EQ(ac::offline::cornerError(points,{100,100}),"REPEATED_CORNERS");
    points={{{10,10},{20,20},{30,30},{40,40}}};
    EXPECT_EQ(ac::offline::cornerError(points,{100,100}),"INSUFFICIENT_PIXEL_AREA");
    points={{{10,10},{10.1f,10},{10.1f,10.1f},{10,10.1f}}};
    EXPECT_EQ(ac::offline::cornerError(points,{100,100}),"INSUFFICIENT_PIXEL_AREA");
    points=good; points[1].x=std::numeric_limits<float>::quiet_NaN();
    EXPECT_EQ(ac::offline::cornerError(points,{100,100}),"NONFINITE_CORNERS");
    points=good; points[0].x=-1;
    EXPECT_EQ(ac::offline::cornerError(points,{100,100}),"CORNERS_OUTSIDE_IMAGE");
    points={{{10,10},{90,10},{30,30},{10,90}}};
    EXPECT_EQ(ac::offline::cornerError(points,{100,100}),"NONCONVEX_CORNERS");
}

TEST(OfflinePerception, MatchesDirectClassesAndPreservesInput) {
    cv::Mat image(600,600,CV_8UC3,cv::Scalar(127,127,127));
    for(int r=0;r<8;++r) for(int c=0;c<8;++c)
        image(cv::Rect(100+50*c,100+50*r,50,50)).setTo(cv::Scalar::all(255*((r+c)%2)));
    // Non-gray BGR cells ensure channel interpretation is exercised too.
    cv::circle(image,{275,275},12,{20,70,230},-1);
    const auto original=image.clone();
    const auto actual=ac::offline::process(image);
    const auto detected=ac::BoardDetector().detect(image);
    ASSERT_TRUE(detected); ASSERT_TRUE(actual.detected); ASSERT_TRUE(actual.observation);
    EXPECT_EQ(detected->corners,actual.detected->corners);
    const auto H=ac::Homography().compute(detected->corners);
    EXPECT_EQ(cv::norm(H,actual.homography,cv::NORM_INF),0);
    const auto rectified=ac::Homography().warp(image,H,800);
    EXPECT_EQ(cv::norm(rectified,actual.rectified,cv::NORM_INF),0);
    std::array<std::array<cv::Mat,8>,8> cells;
    for(int r=0;r<8;++r) for(int c=0;c<8;++c) cells[r][c]=rectified(cv::Rect(c*100,r*100,100,100));
    EXPECT_EQ(ac::PieceDetector().analyzeBoard(cells).cells,actual.observation->cells);
    EXPECT_EQ(cv::norm(image,original,cv::NORM_INF),0);
    std::vector<cv::Point2f> projected;
    cv::perspectiveTransform(std::vector<cv::Point2f>(detected->corners.begin(),detected->corners.end()),projected,H);
    const std::vector<cv::Point2f> expected{{0,0},{800,0},{800,800},{0,800}};
    for(size_t i=0;i<4;++i) EXPECT_LT(cv::norm(projected[i]-expected[i]),.001);
}
