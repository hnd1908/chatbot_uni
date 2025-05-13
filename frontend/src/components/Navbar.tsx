// import { useState } from "react";
// import { Link } from "react-router-dom";
// import { UserButton, SignedIn, SignedOut } from "@clerk/clerk-react";

// export default function Navbar() {
//   const [isOpen, setIsOpen] = useState(false);

//   return (
//     <nav className="bg-white shadow-lg">
//       <div className="max-w-6xl mx-9 px-4 ">
//         <div className="flex justify-between items-center h-16">
//           {/* Menu button */}
//           <button
//             onClick={() => setIsOpen(!isOpen)}
//             className=" text-gray-500 hover:text-gray-900"
//           >
//             <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
//             </svg>
//           </button>

//           {/* Desktop menu */}
//           <div className="hidden md:flex space-x-8">
//             <Link to="/" className="text-gray-700 hover:text-blue-600 px-3 py-2">Home</Link>
//             <SignedIn>
//               <Link to="/chat" className="text-gray-700 hover:text-blue-600 px-3 py-2">Chat</Link>
//               <Link to="/profile" className="text-gray-700 hover:text-blue-600 px-3 py-2">Profile</Link>
//             </SignedIn>
//           </div>

//           {/* Auth buttons */}
//           <div className="flex items-center">
//             <SignedIn>
//               <UserButton afterSignOutUrl="/login" />
//             </SignedIn>
//             <SignedOut>
//               <Link to="/login" className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600">
//                 Sign In
//               </Link>
//             </SignedOut>
//           </div>
//         </div>

//         {/* Mobile menu */}
//         {isOpen && (
//           <div className="md:hidden">
//             <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
//               <Link to="/" className="block px-3 py-2 text-gray-700 hover:text-blue-600">Home</Link>
//               <SignedIn>
//                 <Link to="/chat" className="block px-3 py-2 text-gray-700 hover:text-blue-600">Chat</Link>
//                 <Link to="/profile" className="block px-3 py-2 text-gray-700 hover:text-blue-600">Profile</Link>
//               </SignedIn>
//             </div>
//           </div>
//         )}
//       </div>
//     </nav>
//   );
// }

import { useState } from "react";
import { Link } from "react-router-dom";
import { UserButton, SignedIn} from "@clerk/clerk-react";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 text-2xl text-black z-50 focus:outline-none"
      >
        <img src="/icons8-menu.svg" alt="Menu Icon" className="w-5 h-5" />
      </button>

      <div
        className={`fixed top-0 left-0 h-screen bg-gray-100 text-black transition-all duration-1000 overflow-hidden z-40 ${
          isOpen ? "w-40" : "w-0"
        }`}
      >
        <div className="p-4 mt-16 flex flex-col gap-4">
          <Link to="/" className="hover:text-gray-200">Home</Link>
          <Link to="/chat" className="hover:text-gray-200">Chat</Link>
        </div>
      </div>

      <div className="fixed top-4 right-4">
        <SignedIn>
          <UserButton afterSignOutUrl="/login" />
        </SignedIn>
      </div>
    </>
  );
}