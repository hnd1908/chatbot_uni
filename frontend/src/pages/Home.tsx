import { Link } from "react-router-dom";
import { SignedIn, SignedOut } from "@clerk/clerk-react";

// --- Header ---
function Header() {
  return (
    <header className="bg-[#0A1172] text-white">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center gap-4">
            <img src="\src\assets\logo_uit.png" alt="UIT Logo" className="h-12 w-12" />
            <span className="font-bold text-xl">Tuyển sinh UIT</span>
          </div>
          <nav className="flex gap-6">
            <a  className="hover:underline">Tin tức</a>
            <a  className="hover:underline">Giới thiệu</a>
            <a  className="hover:underline">Liên hệ</a>
          </nav>
        </div>
      </div>
    </header>
  );
}

function HeroSection() {
  return (
    <section className="relative bg-[#0A1172] text-white py-16">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-900 to-transparent opacity-90"></div>
      <div className="relative container mx-auto px-4 flex flex-col items-center z-10">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 text-center">
          Chào mừng đến với Cổng Thông Tin Tuyển Sinh<br />Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)
        </h1>
        <p className="text-lg md:text-xl mb-8 text-center max-w-2xl">
          Tra cứu thông tin tuyển sinh, ngành học, chương trình đào tạo, học bổng và các tin tức mới nhất về UIT.
        </p>
        <div className="flex gap-4">
          <SignedOut>
            <Link
              to="/login"
              className="bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-6 rounded-lg transition"
            >
              Đăng nhập để bắt đầu chat
            </Link>
          </SignedOut>
          <SignedIn>
            <Link
              to="/chat"
              className="bg-green-500 hover:bg-green-600 text-white font-medium py-3 px-6 rounded-lg transition"
            >
              Vào Chatbot
            </Link>
          </SignedIn>
        </div>
      </div>
    </section>
  );
}

// --- News Section ---
function NewsSection() {
  // Dữ liệu mẫu, bạn có thể fetch từ API hoặc props
  const news = [
    {
      title: "UIT công bố đề án tuyển sinh 2025",
      date: "25/05/2025",
      link: "https://tuyensinh.uit.edu.vn/2025-du-kien-phuong-thuc-tuyen-sinh-nam-2025",
      summary: "Đề án tuyển sinh năm 2025 của UIT với nhiều điểm mới về phương thức xét tuyển và ngành học."
    },
    {
      title: "Học bổng UIT Talent 2025",
      date: "20/05/2025",
      link: "https://tuyensinh.uit.edu.vn/2025-thong-bao-hoc-bong-toan-dien-sang-tao-phung-su-nam-2025",
      summary: "UIT tiếp tục triển khai chương trình học bổng UIT Talent dành cho tân sinh viên xuất sắc."
    },
    {
      title: "Ngày hội tư vấn tuyển sinh 2025",
      date: "15/05/2025",
      link: "https://tuyensinh.uit.edu.vn/uit-tham-gia-ngay-hoi-tu-van-tuyen-sinh-mua-thi-2025-co-hoi-hap-dan-cho-he-tre-dam-me-cong-nghe",
      summary: "Tham gia ngày hội để được tư vấn trực tiếp về các ngành học, cơ hội nghề nghiệp và trải nghiệm môi trường UIT."
    }
  ];

  return (
    <section id="news" className="py-12 bg-gray-50">
      <div className="container mx-auto px-4">
        <h2 className="text-2xl font-bold mb-6 text-[#0A1172]">Tin tức tuyển sinh</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {news.map((item, idx) => (
            <a
              key={idx}
              href={item.link}
              className="block bg-white rounded-lg shadow hover:shadow-lg transition p-6"
            >
              <div className="text-sm text-gray-500 mb-2">{item.date}</div>
              <div className="font-semibold text-lg mb-2">{item.title}</div>
              <div className="text-gray-700">{item.summary}</div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

// --- Footer ---
function Footer() {
  return (
    <footer className="bg-[#0A1172] text-white py-8 mt-12">
      <div className="container mx-auto px-4 text-center">
        <div className="mb-2 font-semibold">Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)</div>
        <div>Địa chỉ: Khu phố 6, phường Linh Trung, TP. Thủ Đức, TP.HCM</div>
        <div>Điện thoại: (028) 372 52002 &nbsp;|&nbsp; Email: tuyensinh@uit.edu.vn</div>
        <div className="mt-2 text-sm text-gray-300">© {new Date().getFullYear()} UIT. All rights reserved.</div>
      </div>
    </footer>
  );
}

// --- Trang Home ---
export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-1">
        <HeroSection />
        <NewsSection />
      </main>
      <Footer />
    </div>
  );
}