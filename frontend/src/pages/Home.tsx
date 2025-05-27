import { summary, title } from "framer-motion/client";
import Chatbox from "../components/Chatbox";

// --- Header ---
function Header() {
  return (
    <header className="bg-[#e7e8ff] text-black shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center gap-4">
            <img src="src/assets/logo_uit_cut.png" alt="UIT Logo" className="h-13 w-16" />
            <span className="font-bold text-xl">Tuyển sinh UIT</span>
          </div>
          <nav className="flex gap-6">
            <a href="https://tuyensinh.uit.edu.vn/" className="hover:underline cursor-pointer" target="_blank" rel="noopener noreferrer">Tin tức</a>
            <a href="https://www.uit.edu.vn/tong-quan-ve-truong-dh-cong-nghe-thong-tin" className="hover:underline cursor-pointer" target="_blank" rel="noopener noreferrer">Giới thiệu</a>
            <a href="https://www.uit.edu.vn/lien-he" className="hover:underline cursor-pointer" target="_blank" rel="noopener noreferrer">Liên hệ</a>
          </nav>
        </div>
      </div>
    </header>
  );
}

function HeroSection() {
  return (
    <section className="relative bg-[#343669] text-white py-8">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-900 to-transparent opacity-90"></div>
      <div className="relative container mx-auto px-4 flex flex-col items-center z-10">
        <h1 className="text-3xl md:text-4xl font-bold mb-4 text-center">
          Chào mừng đến với Cổng Thông Tin Tuyển Sinh<br />Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)
        </h1>
        <p className="text-lg md:text-xl mb-8 text-center max-w-2xl">
          Tra cứu thông tin tuyển sinh, ngành học, chương trình đào tạo, học bổng và các tin tức mới nhất về UIT.
        </p>
      </div>
    </section>
  );
}

function NewsSection() {
  const news = [
    {
      title: "UIT công bố đề án tuyển sinh 2025",
      date: "25/05/2025",
      link: "https://tuyensinh.uit.edu.vn/2025-du-kien-phuong-thuc-tuyen-sinh-nam-2025",
      summary: "Đề án tuyển sinh năm 2025 của UIT với nhiều điểm mới về phương thức xét tuyển và ngành học.",
      thumbnail: "https://scontent.fsgn5-9.fna.fbcdn.net/v/t39.30808-6/489818885_1125023986330271_6544787257994631994_n.jpg?stp=dst-jpg_p526x296_tt6&_nc_cat=105&ccb=1-7&_nc_sid=127cfc&_nc_eui2=AeF8dzUS-P_IM3fQqS3BVtGppqa54RhasoOmprnhGFqyg0CihZZ61C7T-IhN9z-6weljOtd0kBNlAz7glqcuFpax&_nc_ohc=VNg_aszuZMgQ7kNvwEZ2ptx&_nc_oc=Adnkg8CVo9BMo-W_5YR5aGNRI5qCJe885-QeDDj6-1vkr7BVpaN3VED02_xz-t2yLvY&_nc_zt=23&_nc_ht=scontent.fsgn5-9.fna&_nc_gid=WRgkL4vJI_n_X44boy6xhg&oh=00_AfKkF1pGopk7CQelSs5wXGG7QRuJGgpp5DsVjjyLHixpMA&oe=683B9DD5"
    },
    {
      title: "Học bổng UIT tài năng 2025",
      date: "09/04/2025",
      link: "https://tuyensinh.uit.edu.vn/2025-thong-bao-hoc-bong-toan-dien-sang-tao-phung-su-nam-2025",
      summary: "UIT tiếp tục triển khai chương trình học bổng UIT Talent dành cho tân sinh viên xuất sắc.",
      thumbnail: "https://scontent.fsgn5-10.fna.fbcdn.net/v/t39.30808-6/487872681_1121212356711434_7826403382184964905_n.jpg?stp=dst-jpg_p526x296_tt6&_nc_cat=107&ccb=1-7&_nc_sid=127cfc&_nc_eui2=AeGZIJuUknzaeY0s1HWqnhQOtYuZyn_sXqG1i5nKf-xeod-maE5FFSAbIAafBwrw_8DDWWCcdP-8Fx_E8cPy98yn&_nc_ohc=OHezndJsxHgQ7kNvwFikrPJ&_nc_oc=AdnkVpuVdH8g6GGDhYm-zixeuDeTPczitd-fzC6GBITNvD3-x1c3I20KPTAyxGCC1sg&_nc_zt=23&_nc_ht=scontent.fsgn5-10.fna&_nc_gid=09AL8Yv2l7EI2dIp2o-9bQ&oh=00_AfIcgky_VHZ2ZDmOm71bKThokeYXW4EgEqMUGEWLrafZQA&oe=683BA8E6"
    },
    {
      title: "Ngày hội tư vấn tuyển sinh 2025",
      date: "17/02/2025",
      link: "https://tuyensinh.uit.edu.vn/uit-tham-gia-ngay-hoi-tu-van-tuyen-sinh-mua-thi-2025-co-hoi-hap-dan-cho-he-tre-dam-me-cong-nghe",
      summary: "Tham gia ngày hội để được tư vấn trực tiếp về các ngành học, cơ hội nghề nghiệp và trải nghiệm môi trường UIT.",
      thumbnail: "https://scontent.fsgn5-14.fna.fbcdn.net/v/t39.30808-6/489011441_1125092149656788_2725190214608033658_n.jpg?stp=dst-jpg_p526x296_tt6&_nc_cat=101&ccb=1-7&_nc_sid=833d8c&_nc_eui2=AeH3pY0t6s4admHkdEFclW6rgf4PQhhYg_GB_g9CGFiD8VFxWtwIHvKiGcoD6Yk2CCxHpCvsFJb7csGDxnvh_e_s&_nc_ohc=GEOHPoqnGisQ7kNvwH6mVWB&_nc_oc=AdkgyH8PCmTDhiUPNVRwzat3rPjPpcTVJCs7p_cjVvgnCpc-ivHcmCcHphQU3_H6NPU&_nc_zt=23&_nc_ht=scontent.fsgn5-14.fna&_nc_gid=jTInaLWoGaVRJuqLjOeDlg&oh=00_AfI7fN_eAy7OgGnwTeO2P9vgMcIP9YOkCLcGORTc-58Rng&oe=683B7494"
    },
    {
      title: "UIT Algo Bootcamp - Kỳ huấn luyện mùa hè | Mùa hè bùng nổ - Đậm chất đam mê",
      date: "08/05/2025",
      link: "https://tuyensinh.uit.edu.vn/uit-algo-bootcamp-ky-huan-luyen-mua-he-mua-he-bung-no-dam-chat-dam-me",
      summary: "Kỳ huấn luyện mùa hè đã chính thức quay trở lại và sẵn sàng cùng bạn tạo nên hành trình bứt phá.",
      thumbnail: "https://tuyensinh.uit.edu.vn/sites/default/files/uploads/files/202505/uit-traihe-poster-2025_1.jpg"
    }
  ];

  return (
    <section id="news" className="py-6 bg-gray-50 rounded-lg">
      <div className="container mx-auto px-4 overflow">
        <h2 className="text-2xl font-bold mb-6 text-[#0A1172] bg-gray-50 sticky top-0 z-10">Tin tức tuyển sinh</h2>
        <div className="flex flex-col gap-6 max-h-[500px] overflow-y-auto pr-1">
          {news.map((item, idx) => (
            <a
              key={idx}
              href={item.link}
              className="flex bg-white rounded-lg shadow hover:shadow-lg transition p-4 gap-4 items-center"
              target="_blank" rel="noopener noreferrer"
            >
              <img src={item.thumbnail} alt={item.title} className="w-24 h-24 object-cover rounded-md flex-shrink-0 border" />
              <div className="flex flex-col">
                <div className="text-sm text-gray-500 mb-1">{item.date}</div>
                <div className="font-semibold text-lg mb-1 line-clamp-2">{item.title}</div>
                <div className="text-gray-700 line-clamp-2">{item.summary}</div>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-[#e7e8ff] text-black py-8 mt-12">
      <div className="container mx-auto px-4 text-center">
        <div className="mb-2 font-semibold">Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)</div>
        <div>Địa chỉ: Khu phố 6, phường Linh Trung, TP. Thủ Đức, TP.HCM</div>
        <div>Điện thoại: (028) 372 52002 &nbsp;|&nbsp; Email: tuyensinh@uit.edu.vn</div>
        <div className="mt-2 text-sm text-gray-500">© {new Date().getFullYear()} UIT. All rights reserved.</div>
      </div>
    </footer>
  );
}

// --- Trang Home ---
export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-1 flex flex-col">
        <HeroSection />
        <div className="container mx-auto px-4 py-12 flex-1 flex flex-col md:flex-row gap-8 items-start">
          {/* News Section - left, scrollable, vertical */}
          <div className="w-full md:w-1/2 h-[600px] pr-2">
            <NewsSection />
          </div>
          {/* Chatbox - right, fixed height, scrollable inside */}
          <div className="w-full md:w-1/2 flex flex-col items-center">
            <div className="w-full max-w-2xl bg-white rounded-xl shadow-lg p-6 border border-blue-100 h-[600px] flex flex-col relative overflow-hidden">
              {/* Logo mờ nền */}
              <img
                src="/src/assets/logo_uit.png"
                alt="UIT Logo Background"
                className="absolute left-1/2 top-1/2 w-2/3 max-w-xs opacity-10 -translate-x-1/2 -translate-y-1/2 pointer-events-none select-none"
                style={{ zIndex: 0 }}
              />
              <h2 className="text-2xl font-bold text-center mb-4 text-blue-900 relative z-10">Chatbot tư vấn tuyển sinh UIT</h2>
              <div className="flex-1 overflow-y-auto relative z-10">
                <Chatbox />
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}