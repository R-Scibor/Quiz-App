import { ReactNode, createContext, useContext, useState } from "react";
import { motion } from "framer-motion";

const CheckboxContext = createContext({
  id: "",
  isChecked: false,
  setIsChecked: (isChecked) => {},
  onChange: () => {},
});

const tickVariants = {
  checked: {
    pathLength: 1,
    opacity: 1,
    transition: {
      duration: 0.2,
      delay: 0.1,
    },
  },
  unchecked: {
    pathLength: 0,
    opacity: 0,
    transition: {
      duration: 0.2,
    },
  },
};

const boxVariants = {
    checked: {
        borderColor: "#DC2525",
        backgroundColor: "#DC2525",
    },
    unchecked: {
        borderColor: "#6b7280", // dark:border-gray-600
        backgroundColor: "transparent",
    }
}

export default function AnimatedCheckbox({ children, id, checked, onChange }) {
  return (
    <label htmlFor={id} className="flex items-center cursor-pointer">
      <CheckboxContext.Provider
        value={{
          id,
          isChecked: checked,
          onChange,
        }}
      >
        {children}
      </CheckboxContext.Provider>
    </label>
  );
}

function CheckboxIndicator() {
  const { id, isChecked, onChange } = useContext(CheckboxContext);

  return (
    <div className="relative flex items-center">
      <input
        type="checkbox"
        className="sr-only"
        onChange={onChange}
        checked={isChecked}
        id={id}
      />
      <motion.div 
        className="h-5 w-5 rounded-md border-2"
        variants={boxVariants}
        initial={false}
        animate={isChecked ? "checked" : "unchecked"}
        transition={{ duration: 0.3 }}
      >
        <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white">
            <motion.svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="3.5"
            stroke="currentColor"
            className="h-3.5 w-3.5"
            initial={false}
            animate={isChecked ? "checked" : "unchecked"}
            >
            <motion.path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4.5 12.75l6 6 9-13.5"
                variants={tickVariants}
            />
            </motion.svg>
        </div>
      </motion.div>
    </div>
  );
}

AnimatedCheckbox.Indicator = CheckboxIndicator;

function CheckboxLabel({ children }) {
  const { isChecked } = useContext(CheckboxContext);

  return (
    <motion.span
      className="relative ml-3 text-gray-700 dark:text-gray-200"
      animate={{
        x: isChecked ? [0, -2, 0] : 0,
      }}
      initial={false}
      transition={{
        duration: 0.2,
        ease: "easeOut",
      }}
    >
      {children}
    </motion.span>
  );
}

AnimatedCheckbox.Label = CheckboxLabel;