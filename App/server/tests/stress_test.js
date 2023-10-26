import http from "k6/http";
import { check, sleep } from "k6";

export default function () {
    const res = http.get("https://twitch-advisor.com")
    check(res, { 'status was 200': (r) => r.status === 200 });
    sleep(1);
}

export const options = {
    vus: 120,
    duration: '10m',
};