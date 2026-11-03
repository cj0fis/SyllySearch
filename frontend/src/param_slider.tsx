import { Group, RangeSlider, Text } from "@mantine/core";
import { useEffect, useState } from "react";

interface ParamSliderProps {
    min: number;
    max: number;
    label: string;
}

export default function ParamSlider({min, max, label}: ParamSliderProps) {
    const [range, setRange] = useState<[number, number]>([min, max]);

    useEffect(() => {
        setRange([min, max]);
    }, [min,max])
    return (
        <Group w="100%" justify="center" >
            <Text w="30%">{label}:</Text>
            <Group>
                <Text w={50}>{range[0].toFixed(2)}</Text>
                <RangeSlider
                    min={min}
                    max={max}
                    value={range}
                    label={null}
                    w={300}
                    onChange={setRange}
                    minRange={min}
                    step={0.01}
                />
                <Text w={50}>{range[1].toFixed(2)}</Text>
            </Group>
        </Group>
    );
}